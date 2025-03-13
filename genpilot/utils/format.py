import yaml


def is_valid_yaml(yaml_string: str) -> bool:
    try:
        yaml.safe_load(yaml_string)
        return True
    except yaml.YAMLError:
        return False
