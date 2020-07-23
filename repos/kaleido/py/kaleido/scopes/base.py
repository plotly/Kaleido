import subprocess
import json
from threading import Lock, Thread
import io
import os
import sys
import locale

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

executable_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'executable',
    'kaleido'
)


class BaseScope(object):
    # Subclasses may override to specify a custom JSON encoder for input data
    _json_encoder = None

    # Tuple of class properties that will be passed as
    # command-line flags to configure chromium
    _chromium_flags = ("disable_gpu",)

    # Tuple of class properties that will be passed as command-line
    # flags to configure scope
    _scope_flags = ()

    def __init__(self, disable_gpu=True):
        # Collect chromium flag properties
        self._disable_gpu = disable_gpu

        # Internal Properties
        self._std_error = io.BytesIO()
        self._std_error_thread = None
        self._proc = None
        self._proc_lock = Lock()

    def __del__(self):
        self._shutdown_kaleido()

    def _build_proc_args(self):
        """
        Build list of kaleido command-line arguments based on current values of
        the properties specified by self._chromium_flags and self._scope_flags

        :return: list of flags
        """
        proc_args = [executable_path, self.scope_name]
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
            proc_args.append(flag)

        return proc_args

    def _collect_standard_error(self):
        """
        Write standard-error of subprocess to the _std_error StringIO buffer.
        Intended to be called once in a background thread
        """
        while True:
            if self._proc is not None:
                val = self._proc.stderr.readline()
                self._std_error.write(val)

    def _ensure_kaleido(self):
        """
        Launch the kaleido subprocess if it is not already running and in a good state
        """
        # Use double-check locking to make sure we only initialize the process
        # from a single thread
        if self._proc is None or self._proc.poll() is not None:
            with self._proc_lock:
                if self._proc is None or self._proc.poll() is not None:
                    # Wait on process if crashed to prevent zombies
                    if self._proc is not None:
                        self._proc.wait()

                    # Reset _std_error buffer
                    self._std_error = io.BytesIO()

                    # Launch kaleido subprocess
                    # Note: shell=True seems to be needed on Windows to handle executable path with
                    # spaces.  The subprocess.Popen docs makes it sound like this shouldn't be
                    # necessary.
                    proc_args = self._build_proc_args()
                    self._proc = subprocess.Popen(
                        proc_args,
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
                            self._get_decoded_std_error()
                        )
                        raise ValueError(message)
                    else:
                        startup_response = json.loads(startup_response_string)
                        if startup_response.get("code", 0) != 0:
                            self._proc.wait()
                            raise ValueError(startup_response.get("message", "Failed to start Kaleido subprocess"))

    def _get_decoded_std_error(self):
        """
        Attempt to decode standard error bytes stream to a string
        """
        std_err_str = None
        try:
            encoding = sys.stderr.encoding
            std_err_str = self._std_error.getvalue().decode(encoding)
        except Exception:
            pass

        if std_err_str is None:
            try:
                encoding = locale.getpreferredencoding(False)
                std_err_str = self._std_error.getvalue().decode(encoding)
            except Exception:
                pass

        if std_err_str is None:
            std_err_str = "Failed to decode Chromium's standard error stream"

        return std_err_str

    def _shutdown_kaleido(self):
        """
        Shut down the kaleido subprocess, if any, and self the _proc property to None
        """
        # Use double-check locking to make sure we only shut down the process
        # a single time when used across threads.
        if self._proc is not None:
            with self._proc_lock:
                if self._proc is not None:
                    if self._proc.poll() is None:
                        # Process still running, close stdin to tell kaleido
                        # to shut down gracefully
                        self._proc.stdin.close()

                    # wait for process to terminate if it was running.
                    # Also prevent zombie process if process crashed
                    # on it's own
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
        """ If True, asks chromium to disable GPU hardware acceleration with --disable-gpu flag"""
        return self._disable_gpu

    @disable_gpu.setter
    def disable_gpu(self, val):
        self._disable_gpu = val
        self._shutdown_kaleido()

    def _perform_transform(self, data, **kwargs):
        """
        Transform input data using the current scope, returning dict response with error code
        whether successful or not.

        :param data: JSON-serializable object to be converted
        :param kwargs: Transform arguments for scope
        :return: Dict of response from Kaleido executable, whether successful or not
        """
        # Ensure that kaleido subprocess is running
        self._ensure_kaleido()

        # Perform export
        export_spec = json.dumps(
            dict(kwargs, data=data),
            cls=self._json_encoder).encode('utf-8')

        # Write to process and read result within a lock so that can be
        # sure we're reading the response to our request
        with self._proc_lock:
            # Reset _std_error buffer
            self._std_error = io.BytesIO()

            # Write and flush spec
            self._proc.stdin.write(export_spec)
            self._proc.stdin.write("\n".encode('utf-8'))
            self._proc.stdin.flush()
            response = self._proc.stdout.readline()

        response_string = response.decode('utf-8')
        if not response_string:
            message = (
                    "Transform failed. Error stream:\n\n" +
                    self._get_decoded_std_error()
            )
            raise ValueError(message)
        try:
            response = json.loads(response_string)
        except JSONDecodeError:
            print("Invalid JSON: " + repr(response_string))
            raise

        return response

    def transform(self, data, **kwargs):
        """
        Transform input data using the current scope

        Subclasses should provide a more helpful docstring

        :param data: JSON-serializable object to be converted
        :param kwargs: Transform arguments for scope
        :return: Transformed value as bytes
        """
        response = self._perform_transform(data, **kwargs)

        # Check for export error
        code = response.pop("code", 0)
        if code != 0:
            message = response.get("message", None)
            raise ValueError(
                "Transform failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        img_string = response.pop("result", None)
        return img_string.encode()
