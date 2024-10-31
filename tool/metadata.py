import ast
import inspect
import datetime
import typing

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    CompletionCreateParams,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types import FunctionDefinition, FunctionParameters
from typing import Tuple, get_type_hints


# [JSON Schema reference](https://json-schema.org/understanding-json-schema/)
json_schema_mapping = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


# https://cookbook.openai.com/examples/orchestrating_agents#executing-routines
# https://openai.com/index/function-calling-and-other-api-updates/
# https://docs.llama-api.com/essentials/function
def chat_tool(func) -> ChatCompletionToolParam:
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
        json_type = json_schema_mapping.get(param_type, "string")
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


def func_metadata(func):
    source = inspect.getsource(func)
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            func_args = [arg.arg for arg in node.args.args]
            func_description = ast.get_docstring(node)
            return func_name, func_args, func_description


def tool_name(func):
    func_name = func.__name__
    module = inspect.getmodule(func)
    module_name = module.__name__
    return func_name, module_name


def build_from_template(file, mapping) -> str:
    with open(file, "r") as f:
        message = f.read()
    replacements = {"{{time}}": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    replacements.update(mapping)
    for placeholder, value in replacements.items():
        message = message.replace(placeholder, value)
    return message
