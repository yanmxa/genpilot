import subprocess
import traceback


def code_executor(language: str, code: str):
    """
    Executes code based on the specified programming language.

    Args:
        language (str): The programming language in which the code is written ('python', 'bash', 'nodejs').
        code (str): The actual code to be executed as a string.

    Returns:
        str: The result of the code execution or an error message.

    Example:

        # Python example
        python_code = "
        def greet():
            return 'Hello from Python!'
        result = greet()
        "
        print(execute_code('python', python_code))

        # Bash example
        bash_code = "echo 'Hello from Bash!'"
        print(execute_code('bash', bash_code))

        # Node.js example
        js_code = "console.log('Hello from Node.js!');"
        print(execute_code('nodejs', js_code))
    """
    try:
        if language.lower() == "python":
            # Create a context dictionary to capture any variables or outputs from exec.
            context = {}
            exec(code, {}, context)  # Execute Python code with the context.
            return context  # Return the context to show the final state of variables (if any).
        elif language.lower() == "bash":
            result = subprocess.run(
                code,
                shell=True,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.stdout
        elif language.lower() == "nodejs" or language.lower() == "javascript":
            result = subprocess.run(
                ["node", "-e", code],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.stdout
        else:
            return f"Unsupported language: {language}"
    except subprocess.CalledProcessError as e:
        print(code)
        return f"Error executing {language} code: {e.stderr}"
    except Exception as e:
        return f"Error: \n {traceback.format_exc()}"
        # return f"code: \n{code}\n{traceback.format_exc()}"
