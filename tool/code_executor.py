import subprocess
import traceback


def code_executor(language, code):
    """
    Executes code based on the specified programming language.

    Args:
        language (str): The programming language in which the code is written ('python', 'bash', 'nodejs').
        code (str): The actual code to be executed as a string.

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
        if language == "python":
            process = subprocess.run(
                ["python3", "-c", code], capture_output=True, text=True
            )
        elif language == "bash":
            process = subprocess.run(
                ["bash", "-c", code], capture_output=True, text=True
            )
        elif language == "nodejs":
            process = subprocess.run(
                ["node", "-e", code], capture_output=True, text=True
            )
        else:
            return "Unsupported language. Please specify 'python', 'bash', or 'nodejs'."

        # Capture output
        output = process.stdout
        error = process.stderr

        # Check for exit code and return both stdout and stderr for debugging
        if process.returncode != 0:
            return f"Execution failed with error:\n{error.strip()}"
        elif not output.strip() and not error.strip():
            return "Execution completed with no output."
        else:
            return output.strip() if output else error.strip()

    except Exception as e:
        # Print the full traceback for debugging
        print("An exception occurred:")
        traceback.print_exc()  # Print the full traceback
        return f"An exception occurred: {str(e)}"
