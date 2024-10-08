class OldKaleidoError(NotImplementedError):
    pass

class BaseScope(object):
    def __init__(self):
        raise OldKaleidoError("Kaleido no longer uses a scope system, BaseScope should not be used.")

