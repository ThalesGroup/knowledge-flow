# Copyright Thales 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from pydantic import ValidationError
from pydantic_settings import BaseSettings
import yaml
from typing import Dict

from knowledge_flow_app.common.structures import Configuration

logger = logging.getLogger(__name__)


def parse_server_configuration(configuration_path: str) -> Configuration:
    """
    Parses the server configuration from a YAML file.

    Args:
        configuration_path (str): The path to the configuration YAML file.

    Returns:
        Configuration: The parsed configuration object.
    """
    with open(configuration_path, "r") as f:
        try:
            config: Dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error while parsing configuration file {configuration_path}: {e}")
            exit(1)
    return Configuration(**config)


def get_embedding_model_name(embedding_model: object) -> str:
    """
    Returns a clean string name for the embedding model, even if wrapped inside a custom class.
    """
    if hasattr(embedding_model, "model"):
        inner = getattr(embedding_model, "model")
        return getattr(inner, "model", type(inner).__name__)
    return getattr(embedding_model, "model", type(embedding_model).__name__)


def validate_settings_or_exit(cls: type[BaseSettings], name: str = "Settings") -> BaseSettings:
    try:
        return cls()
    except ValidationError as e:
        logger.critical(f"❌ Invalid {name}:")
        for error in e.errors():
            field = error.get("loc", ["?"])[0]
            msg = error.get("msg", "")
            logger.critical(f"   - Missing or invalid: {field} → {msg}")
        logger.critical("📌 Tip: Check your .env file or environment variables.")
        raise SystemExit(1)
