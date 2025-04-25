import rich
import yaml
import sys
from rich.syntax import Syntax


def tool_call_validator(tool_name, func_args):
    if tool_name != "yaml_applier":
        return

    if "yaml" not in func_args:
        return "yaml key is required"

    cluster = "default"
    if "cluster" in func_args:
        cluster = func_args["cluster"]

    if "yaml" in func_args and not isinstance(func_args["yaml"], str):
        return "yaml value must be a string"

    console = rich.get_console()
    # Print YAML in a code block with syntax highlighting
    try:
        yaml_data = yaml.safe_load(func_args["yaml"])
        yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
        console.print(syntax)
    except yaml.YAMLError as e:
        return f"Invalid YAML format: {e}"

    # Human-in-the-loop validation
    user_input = (
        console.input(
            f"  🛠  Cluster - [yellow]{cluster}[/yellow] ⎈ Proceed with this YAML? (yes/no): "
        )
        .strip()
        .lower()
    )

    if user_input in ["no", "n"]:
        console.print("[red]Exiting process.[/red]")
        sys.exit(0)  # Exit the process
    elif user_input in ["yes", "y"]:
        return None  # Continue execution
    else:
        return user_input  # Return the input if it's not "yes" or "no"
