from enum import Enum


class StatusCode(Enum):
    ANSWER = 401
    THOUGHT = 403
    OBSERVATION = 405
    NONE = 404
    ERROR = 501
    ACTION_FORBIDDEN = 502
