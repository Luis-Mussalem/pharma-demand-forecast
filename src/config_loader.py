from pathlib import Path
import yaml


def load_config(config_path: Path) -> dict:
    """
    Loads pipeline configuration from a YAML file.

    Parameters
    ----------
    config_path : Path
        Path to the YAML configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    return config

def load_schema_version(schema_path: Path) -> dict:
    """
    Loads schema version configuration from a YAML file.

    Parameters
    ----------
    schema_path : Path
        Path to schema version YAML file.

    Returns
    -------
    dict
        Parsed schema version configuration.
    """

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r") as file:
        schema_config = yaml.safe_load(file)

    return schema_config