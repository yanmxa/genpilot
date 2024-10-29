from enum import Enum


class StatusCode(Enum):
    ACTION = 400
    ANSWER = 401
    THOUGHT = 403
    OBSERVATION = 405
    NONE = 404
    ERROR = 501
    ACTION_FORBIDDEN = 502
