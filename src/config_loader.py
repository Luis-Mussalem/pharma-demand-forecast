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