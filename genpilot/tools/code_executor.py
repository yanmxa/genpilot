import subprocess
import traceback
from rich.syntax import Syntax


import os
import sys
import subprocess


def code_executor(language, code):
    """
    The code_executor executes code or bash command based on the specified programming language: 'python', 'bash', 'nodejs'.

    Args:
        language (str): The programming language in which the code is written ('python', 'bash', 'nodejs').
        code (str): The actual code to be executed as a string. Like shell command(kubectl, oc, ...), python code, and nodejs code.

    Returns:
        str: The result of the code execution or an error message.

    Example:

        # Python example
        python_code = f"def greet():\n    return 'Hello from Python!'\nresult = greet()"
        print(execute_code('python', python_code))

        # Bash example
        bash_code = "echo 'Hello from Bash!'"
        print(execute_code('bash', bash_code))

        # Node.js example
        js_code = "console.log('Hello from Node.js!');"
        print(execute_code('nodejs', js_code))
    """
    try:
        if language == "python" or language == "python3":
            # version_process = subprocess.run(
            #     ["python3", "--version"], text=True, capture_output=True
            # )
            # print("Python version:", version_process.stdout.strip())
            # backend_code = "import matplotlib; print(matplotlib.get_backend())"
            # backend_process = subprocess.run(
            #     ["python3", "-c", backend_code], text=True, capture_output=True
            # )
            # print("Matplotlib backend:", backend_process.stdout.strip())
            # Execute Python code
            process = subprocess.run(
                [language, "-c", code], text=True, capture_output=True
            )
        elif language == "bash":
            process = subprocess.run(
                ["bash", "-c", code],
                capture_output=True,
                text=True,
                # stdout=subprocess.PIPE,
            )
        elif language == "nodejs":
            process = subprocess.run(
                ["node", "-e", code],
                # capture_output=True,
                text=True,
                # stdout=subprocess.PIPE,
            )
        else:
            return "Unsupported language. Please specify 'python', 'bash', or 'nodejs'."

        # Capture output
        output = process.stdout
        error = process.stderr

        # Check for exit code and return both stdout and stderr for debugging
        if not output and not error:
            return "Execution completed with no output."
        return output.strip() if output else f"{error.strip()}"

    except Exception as e:
        # Print the full traceback for debugging
        print("An exception occurred:")
        traceback.print_exc()  # Print the full traceback
        return f"An exception occurred: {str(e)}"


def terminal_code_executor_printer(agent, func_name, func_args):
    import rich

    console = rich.get_console()
    console.print(f"  🛠  [yellow]{func_args['language']}[/yellow]")
    print()
    console.print(
        Syntax(
            func_args["code"],
            func_args["language"],
            theme="monokai",
            line_numbers=True,
        )
    )
