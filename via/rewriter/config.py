"""Reading config for `pywb`"""

import os.path
import os


class Configuration:
    ENV_PREFIX = "VIA_"
    OPTIONS = ("ignore_prefixes", "h_embed_url")
    MULTI_VALUE_OPTIONS = ("ignore_prefixes",)

    @classmethod
    def parse(cls):
        """Parse options from environment variables."""

        config = {}

        for option in cls.OPTIONS:
            env_name = cls.ENV_PREFIX + option.upper()

            value = os.environ.get(env_name)
            if value:
                config[option] = value

        for option in cls.MULTI_VALUE_OPTIONS:
            config[option] = cls._multiline(config[option])

        config['base_dir'] = cls._config_dir()

        return config

    @classmethod
    def _config_dir(cls):
        config_file = os.path.abspath(os.environ['PYWB_CONFIG_FILE'])
        os.environ['PYWB_CONFIG_FILE'] = config_file
        config_dir = os.path.dirname(config_file)

        return config_dir

    @classmethod
    def _multiline(cls, value):
        return [part for part in [p.strip() for p in value.split(",")] if part]
