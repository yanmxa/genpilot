import inspect
from openai.types.chat import ChatCompletionToolParam
from openai.types import FunctionDefinition, FunctionParameters
from typing import Tuple, get_type_hints

# [JSON Schema reference](https://json-schema.org/understanding-json-schema/)
json_type_mapping = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


# https://cookbook.openai.com/examples/orchestrating_agents#executing-routines
def function_to_schema(func) -> dict:
    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = json_type_mapping.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


# https://cookbook.openai.com/examples/orchestrating_agents#executing-routines
# https://openai.com/index/function-calling-and-other-api-updates/
# https://docs.llama-api.com/essentials/function
def func_to_param(func) -> ChatCompletionToolParam:
    try:
        parameters = inspect.signature(func).parameters
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    func_parameters: FunctionParameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    type_hints = get_type_hints(func)
    for param_name, param in parameters.items():
        param_type = type_hints.get(param_name, str)
        # Mapping to JSON schema types
        json_type = json_type_mapping.get(param_type, "string")
        property_info = {
            "type": json_type,
            "description": f"{param_name} parameter",
        }
        func_parameters["properties"][param_name] = property_info
        if param.default == inspect.Parameter.empty:
            func_parameters["required"].append(param_name)

    return ChatCompletionToolParam(
        type="function",
        function=FunctionDefinition(
            name=func.__name__,
            description=(func.__doc__ or "").strip(),
            parameters=func_parameters,
            strict=True,
        ),
    )


# def sample_function(param_1, param_2, the_third_one: int, some_optional="John Doe"):
#     """
#     This is my docstring. Call this function when you want.
#     """
#     print("Hello, world")


# schema = function_to_schema(sample_function)
# import json

# print(json.dumps(schema, indent=2))
