import boto3
import logging
import os
import re
from typing import Any

from botocore.exceptions import ClientError
from box import Box
from dotenv import find_dotenv, load_dotenv
from tomlkit import parse, items

logger = logging.getLogger(__name__)


class Settings:
    """Settings class that can be accessed using either dict notation (settings.get('abc')) or
    dot notation (settings.snowflake.password). Reads from toml file and requires a table/section called 'default', along with
    a table/section for each environment, e.g. [local], [sbx], [prd]. Supports nested tables with dot notation, e.g. [local.snowflake]
    """

    TOML_TO_BUILTIN_MAP = {
        items.String: str,
        items.Bool: bool,
        items.Integer: int,
        items.Float: float,
    }

    INTERNAL_ATTRS = ["_store", "_ssm"]

    def __init__(self, config_filepath: str = "settings.toml", env: str = os.getenv("ENV")):
        self._store = Box()
        self._ssm = boto3.client("ssm", region_name="us-east-1")

        # Load from .env file if exists. Will set env variables for use in .ini files.
        load_dotenv(find_dotenv(usecwd=True), verbose=True)

        self.read(config_filepath, env)

    def read(self, config_filepath: str, env: str):
        if not os.path.exists(config_filepath):
            raise OSError("Could not load the default or provided settings file.")

        with open(config_filepath, "r") as f:
            settings_data = parse(f.read())

        if "default" not in settings_data:
            raise Exception("Settings file missing required section 'default'")

        for table, items in settings_data.items():
            if table.startswith(env) or table == "default":
                for k, v in items.items():
                    self._set_value_from_config(k, v)

    def _set_value_from_config(self, name: str, value: Any, parent: str = None):
        if name.upper() in os.environ and not parent:
            self.set_attr(name, os.getenv(name.upper()), parent)
        elif parent and f"{parent.upper()}_{name.upper()}" in os.environ:
            self.set_attr(name, os.getenv(f"{parent.upper()}_{name.upper()}"), parent)
        elif isinstance(value, dict):
            for k, v in value.items():
                self._set_value_from_config(k, v, name)
        elif value.startswith("${") and value.endswith("}"):
            # Expecting environment variable with the value between ${}
            var_name = re.findall(r'\${(.*?)}', value)[0]

            if var_name in os.environ:
                self.set_attr(name, os.getenv(var_name), parent)
        elif value.startswith("ssm:"):
            try:
                param = self._ssm.get_parameter(
                    Name=value.replace("ssm:", ""),
                    WithDecryption=True
                )

                if param.get("Parameter"):
                    self.set_attr(name, param["Parameter"]["Value"], parent)
            except ClientError as e:
                # Best effort to load parameter
                logger.error(e)
        else:
            self.set_attr(name, value, parent)

    def set_attr(self, name: str, value: str, parent: str = None):
        if type(value) in self.TOML_TO_BUILTIN_MAP:
            value = self.TOML_TO_BUILTIN_MAP[type(value)](value)

        if isinstance(value, dict):
            value = Box(value)

        if parent:
            if parent not in self._store:
                self._store[parent] = Box()

            self._store[parent][name] = value
        else:
            self._store[name] = value

    def __dir__(self):
        """Enable auto-complete for code editors"""
        return (
            self.INTERNAL_ATTRS
            + [k.lower() for k in self._store.keys()]
        )

    def __getattr__(self, name):
        """Allow getting keys from self._store using dot notation"""
        value = getattr(self._store, name)
        return value

    def __setattr__(self, name, value):
        """Allow `settings.FOO = 'value'` while keeping internal attrs."""
        if name in self.INTERNAL_ATTRS:
            super(Settings, self).__setattr__(name, value)
        else:
            self.set_attr(name, value)

    def __contains__(self, item):
        """Respond to `item in settings`"""
        return item.upper() in self._store or item.lower() in self._store

    def __getitem__(self, item):
        """Allow getting variables as dict keys `settings['KEY']`"""
        value = self._store.get(item)
        if value is None:
            raise KeyError(f"{item} does not exist")
        return value

    def __setitem__(self, key, value):
        """Allow `settings['KEY'] = 'value'`"""
        self.set_attr(key, value)

    def __iter__(self):
        """Redirects to store object"""
        yield from self._store

    def items(self):
        """Redirects to store object"""
        return self._store.items()

    def keys(self):
        """Redirects to store object"""
        return self._store.keys()

    def values(self):
        """Redirects to store object"""
        return self._store.values()
