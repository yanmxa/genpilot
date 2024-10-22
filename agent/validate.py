from enum import Enum
import json
import re


class StatusCode(Enum):
    ACTION = 400  # Only action exists
    ANSWER = 401  # Only answer exists
    NONE = 404  # Neither action nor answer exists
    INVALID_JSON = 500  # Error: Invalid JSON
    ERROR = 501
    ACTION_FORBIDDEN = 502


def check(input_string):
    try:
        json_match = re.search(r"{.*}", input_string, re.DOTALL)
        if json_match:
            json_part = json_match.group(0)
            data = json.loads(json_part)
        else:
            raise ValueError(
                "The response must be a valid JSON object and no other format."
            )

        has_action = "action" in data and data["action"] is not None
        has_answer = "answer" in data and data["answer"] is not None
        has_thought = "thought" in data and data["thought"] is not None

        if not has_thought and has_answer:
            return StatusCode.ANSWER, None, data["answer"]

        if not has_thought:
            raise ValueError("No thought provided.")
        if has_action and has_answer:
            raise ValueError("Conflict: both action and answer exist.")
        if not has_action and not has_answer:
            raise ValueError("No action or answer provided.")
        if has_action:
            action = data["action"]
            has_func = "name" in action and action is not None
            has_args = "args" in action and action is not None
            has_edit = "edit" in action and action is not None
            if not has_func or not has_args or not has_edit:
                raise ValueError("No name, args, or edit provided in action")
            return StatusCode.ACTION, data["thought"], data["action"]
        if has_answer:
            return StatusCode.ANSWER, data["thought"], data["answer"]

        # Default return if none of the cases match (shouldn't occur)
        return StatusCode.NONE, data["thought"], None

    except json.JSONDecodeError as e:
        return StatusCode.INVALID_JSON, None, f"Response an invalid JSON: {e}"
    except ValueError as e:
        return StatusCode.ERROR, None, f"Response error: {e}"
