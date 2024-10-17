import ast
import inspect


def extract_function_info(func):
    # Get the source code of the function
    source = inspect.getsource(func)

    # Parse the source code into an AST
    tree = ast.parse(source)

    # Find the first function definition in the AST
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # Extract function name
            function_name = node.name

            # Extract function parameters
            parameters = [arg.arg for arg in node.args.args]

            # Extract docstring
            docstring = ast.get_docstring(node)

            return function_name, parameters, docstring


# name, params, doc = extract_function_info(wikipedia)
# print(f"Function Name: {name}")
# print(f"Parameters: {params}")
# print(f"Docstring: {doc}")
