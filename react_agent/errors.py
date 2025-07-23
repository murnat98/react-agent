class ReActError(Exception):
    pass


class LLMQueryError(ReActError):
    pass


class InvalidActionError(ReActError):
    pass
