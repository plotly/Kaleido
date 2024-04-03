from kaleido.scopes.base import BaseScope, which
import base64


class MermaidScope(BaseScope):
    """
    Scope for transforming Mermaid figures to static images
    """
    _all_formats = ("svg")
    _text_formats = ("svg")

    _scope_flags = ()
    _scope_chromium_args = ("--no-sandbox",)

    def __init__(self, **kwargs):
        pass
        super(MermaidScope, self).__init__(**kwargs)


    @property
    def scope_name(self):
        return "mermaid"

    
    def transform(self, markdown, format):
        """
        Convert a Mermaid markdown into a static image
        """
        response = self._perform_transform(markdown)

        code = response.get("code", 0)
        if code != 0:
            message = response.get("message", None)
            raise ValueError(
                "Transform failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        img = response.get("result").encode("utf-8")

        if format not in self._text_formats:
            img = base64.b64decode(img)

        return img