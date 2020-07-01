import subprocess
import json
import base64
from json import JSONDecodeError
from threading import Lock, Thread
import io
import os
import sys

executable_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'executable', 'kaleido')


class BaseScope(object):
    _json_encoder = None
    _text_formats = ("svg",)
    _chromium_flags = ("disable_gpu",)
    _scope_flags = ()

    def __init__(self, disable_gpu=True):

        # Collect chromium flags
        self._disable_gpu = disable_gpu

        # to_image-level default values
        self.default_format = "png"
        self.default_width = 700
        self.default_height = 500
        self.default_scale = 1

        # Properties
        self._std_error = io.StringIO()
        self._std_error_thread = None
        self._proc_args = None

        # Build process arguments list
        self._update_proc_args()

        # Launch subprocess
        self._proc = None
        self._proc_lock = Lock()

    def __del__(self):
        self._shutdown_kaleido()

    def _update_proc_args(self):
        self._proc_args = [executable_path, self.scope_name]
        for k in self._chromium_flags + self._scope_flags:
            v = getattr(self, k)
            if v is True:
                flag = '--' + k.replace("_", "-")
            elif v is False or v is None:
                # Logical flag set to False, don't include flag or argument
                continue
            else:
                # Flag with associated value
                flag = '--' + k.replace("_", "-") + "=" + repr(str(v))
            self._proc_args.append(flag)

    def _collect_standard_error(self):
        while True:
            if self._proc is not None:
                val = self._proc.stderr.readline().decode('utf-8')
                self._std_error.write(val)

    def _ensure_kaleido(self):
        if self._proc is None or self._proc.poll() is not None:
            with self._proc_lock:
                if self._proc is None or self._proc.poll() is not None:
                    # Wait on process if crashed to prevent zombies
                    if self._proc is not None:
                        self._proc.wait()

                    # Reset _std_error buffer
                    self._std_error = io.StringIO()

                    # Launch kaleido subprocess
                    # Note: shell=True seems to be needed on Windows to handle executable path with
                    # spaces.  The subprocess.Popen docs makes it sound like this shouldn't be
                    # necessary.
                    self._update_proc_args()
                    self._proc = subprocess.Popen(
                        self._proc_args,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=sys.platform == "win32"
                    )

                    # Set up thread to asynchronously collect standard error stream
                    if self._std_error_thread is None:
                        self._std_error_thread = Thread(target=self._collect_standard_error)
                        self._std_error_thread.setDaemon(True)
                        self._std_error_thread.start()

                    # Read startup message and check for errors
                    startup_response_string = self._proc.stdout.readline().decode('utf-8')
                    if not startup_response_string:
                        message = (
                            "Failed to start Kaleido subprocess. Error stream:\n\n" +
                            self._std_error.getvalue()
                        )
                        raise ValueError(message)
                    else:
                        startup_response = json.loads(startup_response_string)
                        if startup_response.get("code", 0) != 0:
                            self._proc.wait()
                            raise ValueError(startup_response.get("message", "Failed to start Kaleido subprocess"))

    def _shutdown_kaleido(self):
        if self._proc is not None:
            with self._proc_lock:
                if self._proc is not None:
                    if self._proc.poll() is None:
                        # Process still running, close stdin to tell kaleido to shut down gracefully
                        self._proc.stdin.close()

                    # wait for process to terminate if it was running, also prevent zombie process if
                    # process crashed on it's own
                    try:
                        self._proc.wait(timeout=2.0)
                    except:
                        # We tried to wait! Moving on...
                        pass

                    # Clear _proc property
                    self._proc = None

    @property
    def scope_name(self):
        raise NotImplementedError

    # Flag property methods
    @property
    def disable_gpu(self):
        return self._disable_gpu

    @disable_gpu.setter
    def disable_gpu(self, val):
        self._disable_gpu = val
        self._shutdown_kaleido()

    def to_image(self, figure, format=None, width=None, height=None, scale=None):

        # Infer defaults
        format = format if format is not None else self.default_format
        width = width if width is not None else self.default_width
        height = height if height is not None else self.default_height
        scale = scale if scale is not None else self.default_scale

        # Ensure that kaleido subprocess is running
        self._ensure_kaleido()

        # Perform export
        export_spec = json.dumps({
            "figure": figure,
            "format": format,
            "width": width,
            "height": height,
            "scale": scale,
        }, cls=self._json_encoder).encode('utf-8')

        # Write to process and read result within a lock so that can be
        # sure we're reading the response to our request
        with self._proc_lock:
            # Reset _std_error buffer
            self._std_error = io.StringIO()

            # Write and flush spec
            self._proc.stdin.write(export_spec)
            self._proc.stdin.write("\n".encode('utf-8'))
            self._proc.stdin.flush()
            response = self._proc.stdout.readline()

        response_string = response.decode('utf-8')
        if not response_string:
            message = (
                    "Image export failed. Error stream:\n\n" +
                    self._std_error.getvalue()
            )
            raise ValueError(message)
        try:
            response = json.loads(response_string)
        except JSONDecodeError:
            print("Invalid JSON: " + repr(response_string))
            raise
        code = response.pop("code", 0)

        # Check for export error
        if code != 0:
            message = response.get("message", None)
            raise ValueError(
                "Image export failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        # Export successful
        img_string = response.pop("result", None)
        if format in self._text_formats:
            img = img_string.encode()
        else:
            img = base64.decodebytes(img_string.encode())
        return img
