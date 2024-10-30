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
    int: "number",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
}


def chat_tool(func) -> tuple[str, str, ChatCompletionToolParam]:
    module = inspect.getmodule(func)
    func_name = func.__name__
    module_name = module.__name__
    func_description = func.__doc__

    parameters = inspect.signature(func).parameters

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

    return (
        func_name,
        module_name,
        ChatCompletionToolParam(
            type="function",
            function=FunctionDefinition(
                name=func_name,
                description=func_description,
                parameters=func_parameters,
                strict=True,
            ),
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


def extract_tool(func):
    func_name = func.__name__
    module = inspect.getmodule(func)
    module_name = module.__name__
    schema = function_to_schema(func)
    return func_name, module_name, schema


# https://openai.com/index/function-calling-and-other-api-updates/
# https://docs.llama-api.com/essentials/function
def function_to_schema(func):
    func_name = func.__name__
    docstring = func.__doc__ or "No description provided."
    parameters = inspect.signature(func).parameters
    type_hints = get_type_hints(func)

    schema = {
        "name": func_name,
        "description": docstring.strip(),
        "parameters": {"type": "object", "properties": {}, "required": []},
    }

    for param_name, param in parameters.items():
        param_type = type_hints.get(param_name, str).__name__

        property_info = {
            "type": param_type.lower(),
            "description": f"{param_name} parameter",
        }

        schema["parameters"]["properties"][param_name] = property_info

        if param.default == inspect.Parameter.empty:
            schema["parameters"]["required"].append(param_name)

    return schema


def build_from_template(file, mapping) -> str:
    with open(file, "r") as f:
        message = f.read()
    replacements = {"{{time}}": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    replacements.update(mapping)
    for placeholder, value in replacements.items():
        message = message.replace(placeholder, value)
    return message
