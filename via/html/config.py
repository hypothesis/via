"""Reading and merging config for `pywb` from the CLI and config files."""

import os.path
from argparse import ArgumentParser
from configparser import ConfigParser

from pkg_resources import resource_filename


class Configuration:
    DEFAULT_PORT = 9084

    CUSTOM_PARAMS = {
        ("-c", "--config-file"): {"help": "Via config INI file", "required": True}
    }

    OVERRIDE_PARAMS = {
        ("-p", "--port"): {"help": f"Port to listen on (default {DEFAULT_PORT})"},
        ("-b", "--bind"): {"help": "Address to listen on (default 0.0.0.0)"},
        ("-t", "--threads"): {"help": "Number of threads to use (default 4)"},
        ("--debug",): {"help": "Enable debug mode", "action": "store_true"},
    }

    EXPECTED_INI_SECTIONS = ("app:main", "config")

    @classmethod
    def parse(cls):
        cli_args = cls._parse_cli()
        config = cls._parse_ini(cli_args.pop("config_file"))

        ini_args = config.pop("app:main")
        ini_args["directory"] = resource_filename("via", "html/conf/live_collection")
        ini_args.update(cli_args)

        return list(cls._deparse(ini_args)), config["config"]

    @classmethod
    def _deparse(cls, options):
        for key, value in options.items():
            if value == "False":
                continue

            yield f"--{key}"

            if value != "True":
                yield value

    @classmethod
    def _parse_ini(cls, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Cannot find config file '{config_file}'")

        ini_parser = ConfigParser()
        ini_parser.read(config_file)

        final = {}

        for section in cls.EXPECTED_INI_SECTIONS:
            if section not in ini_parser:
                raise ValueError(f"Expected section [{section}] in config")

            final[section] = dict(ini_parser[section])

        final["config"]["ignore_prefixes"] = cls._multiline(
            final["config"]["ignore_prefixes"]
        )

        return final

    @classmethod
    def _multiline(cls, value):
        return [part for part in [p.strip() for p in value.split("\n")] if part]

    @classmethod
    def _parse_cli(cls):
        parser = ArgumentParser()
        for names, kwargs in cls.OVERRIDE_PARAMS.items():
            parser.add_argument(*names, **kwargs)

        for names, kwargs in cls.CUSTOM_PARAMS.items():
            parser.add_argument(*names, **kwargs)

        args = vars(parser.parse_args())

        return {k: v for k, v in args.items() if v not in (None, False)}
