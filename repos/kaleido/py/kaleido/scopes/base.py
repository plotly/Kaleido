import subprocess
import json
import base64
from threading import Lock

# TODO: compute location in wheel
kaleido_path = "/media/jmmease/SSD11/kaleido/repos/build/kaleido/kaleido"


class BaseScope(object):
    _json_encoder = None

    def __init__(self, disable_gpu=True, **kwargs):

        # TODO: Validate disable_gpu
        kwargs['disable_gpu'] = disable_gpu

        # Build process arguments list
        self.proc_args = [kaleido_path, self.scope_name]
        for k, v in kwargs.items():
            if v is True:
                flag = '--' + k.replace("_", "-")
            elif v is False or v is None:
                # Logical flag set to False, don't inlude argument
                continue
            else:
                # Flag with associated value
                flag = '--' + k.replace("_", "-") + "=" + repr(v)
            self.proc_args.append(flag)

        # Launch subprocess
        self._proc = None
        self._launch_kaleido()
        self._proc_lock = Lock()

    def _launch_kaleido(self):
        if self._proc is not None:
            # TODO: shut down prior proc if running
            pass

        print(self.proc_args)
        # Launch kaleido subprocess
        self._proc = subprocess.Popen(
            self.proc_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            # TODO: Hide stderr
            #, stderr=subprocess.PIPE
        )

    @property
    def scope_name(self):
        raise NotImplementedError

    def to_image(self, figure, format="png", width=700, height=500, scale=1):
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
            # Write and flush spec
            self._proc.stdin.write(export_spec)
            self._proc.stdin.write("\n".encode('utf-8'))
            self._proc.stdin.flush()
            response = self._proc.stdout.readline()

        response = json.loads(response.decode('utf-8'))
        code = response.pop("code", None)
        # Check for export error

        if code is not None:
            message = response.get("message", None)
            raise ValueError(
                "Image export failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        # Export successful
        img_string = response.pop("result", None)
        if format == 'svg':
            img = img_string.encode()
        else:
            img = base64.decodebytes(img_string.encode())
        return img
