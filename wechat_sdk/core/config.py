from importlib import resources
from pathlib import Path
from typing import Any

import yaml


CONFIG_PACKAGE = "wechat_sdk.config"


def load_yaml(filename: str) -> Any:
    with resources.files(CONFIG_PACKAGE).joinpath(filename).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_yaml_path(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}
