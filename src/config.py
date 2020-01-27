from typing import Dict
import yaml
import os


class ConfigProvider:

    QUESTION_DEFAULTS_PATH = "question_defaults.yml"

    @staticmethod
    def get_question_defaults() -> Dict[str, object]:
        root = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(root, ConfigProvider.QUESTION_DEFAULTS_PATH)
        with open(path, "r") as file:
            cfg = yaml.load(file, Loader=yaml.Loader)
            return cfg
