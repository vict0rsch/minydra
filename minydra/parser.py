import ast
import os
import pathlib
import re
import sys
from typing import Any, List, Optional, Union

from minydra.dict import MinyDict
from minydra.exceptions import MinydraWrongArgumentException
from minydra.utils import resolve_path


class Parser:
    """
    Minydra Parser: reads `sys.argv[1:]` into a `minydra.MinyDict`.

    Immediately runs `self._parse_args()`: storing a dictionnary of arguments
    in `self.dict_args` and a `minydra.MinyDict` of arguments in `self.args`.
    """

    known_types = {
        "bool",
        "int",
        "float",
        "str",
    }

    type_separator = "___"

    def __init__(
        self,
        verbose=0,
        allow_overwrites=False,
        warn_overwrites=True,
        parse_env=True,
        warn_env=True,
        defaults=None,
        strict=True,
        keep_special_kwargs=True,
    ) -> None:
        """
        Create a Minydra Parser to parse arbitrary commandline argument as:

            * `key=value`
            * `positiveArg` (set to `True`)
            * `-negativeArg` (set to `False`)

        Args:
            verbose (int, optional): Wether to print received system arguments.
                Defaults to 0.
            allow_overwrites (bool, optional): Wether to allow for repeating arguments
                in the command line. Defaults to True.
            warn_overwrites (bool, optional): Wether to print a waring in case of a
                repeated argument (if that is allowed). Defaults to True.
            parse_env (bool, optional): Wether to parse environment variables specified
                as key or value in the command line. Defaults to True.
            warn_env (bool, optional): Wether to print a warning in case an environment
                variable is parsed but no value is found. Defaults to True.
            defaults (Union[str, dict, MinyDict], optional): Default arguments
                a (Miny)dict or a path to a file that `minydra.MinyDict` will be able to
                load (as `json`, `pickle` or `yaml`). Can also be provided with the
                special `@defaults=<value>` command-line argument. Defaults to None.
            strict (bool, optional): Wether to raise an error if an unknown argument is
                passed and `defaults` was provided. Can also be provided with the
                special `@strict=<true|false>` command-line argument. Defaults to True.
            keep_special_kwargs (bool, optional): Wether to keep special keywords like
                `@defaults` and `@strict` in the parsed arguments. Defaults to True.
        """
        super().__init__()

        self.conf = MinyDict()
        # store initial arguments in a conf object to be able to
        # retrieve them later and most importantly to be able to
        # parse them in the `_parse_conf()` method
        self.conf.verbose = verbose
        self.conf.allow_overwrites = allow_overwrites
        self.conf.warn_overwrites = warn_overwrites
        self.conf.parse_env = parse_env
        self.conf.warn_env = warn_env
        self.conf.defaults = defaults
        self.conf.strict = strict
        self.conf.keep_special_kwargs = keep_special_kwargs

        self._argv = sys.argv[1:]
        self._parse_args()
        self._print("sys.argv:", self._argv)

        # defaults are provided
        if self.conf.defaults is not None or self.args["@defaults"]:
            # load defaults as a MinyDict
            default = self.load_defaults(self.args["@defaults"] or self.conf.defaults)
            # resolve existing args to properly override nested defaults
            args = self.args.deepcopy().resolve()

            args_defaults = args["@defaults"]
            args_strict = args["@strict"]

            # clean args
            if args_defaults is not None:
                del args["@defaults"]
            if args_strict is not None:
                self.conf.strict = args["@strict"]
                del args["@strict"]

            # update defaults from command-line args
            self.args = default.update(args, strict=self.conf.strict)

            # bring back special (@) kwargs if need be
            if self.conf.keep_special_kwargs:
                if args_defaults is not None:
                    self.args["@defaults"] = args_defaults
                if args_strict is not None:
                    self.args["@strict"] = args_strict

        # clean up special (@) kwargs if need be
        if not self.conf.keep_special_kwargs:
            for k in self.conf:
                self.args.pop(f"@{k}", None)

    @staticmethod
    def load_defaults(default: Union[str, dict, MinyDict]):
        """
        Set the default keys from `defaults`:

        * str/path -> must point to a yaml/json/pickle file then
            MinyDict.from_X will be used
        * dict -> Convert that dictionnary to a resolved MinyDict
        * list -> Recursively calls load_defaults on each element, then
            sequentially update an (initially empty) MinyDict to allow
            for hierarchical defaults.

        Args:
            allow (Union[str, dict, MinyDict]): The set of allowed keys as a
                (Miny)dict or a path to a file that `minydra.MinyDict` will be able to
                load (as `json`, `pickle` or `yaml`)
        """
        # `defaults` is a path: load it with MinyDict.from_X
        if isinstance(default, (str, pathlib.Path)):
            # resolve path to file
            default = resolve_path(default)
            # ensure it exists
            assert default.exists()
            assert default.is_file()
            # check for known file formats
            if default.suffix not in {".json", ".yaml", ".yml", ".pickle", ".pkl"}:
                raise ValueError(f"{str(default)} is not a valid file extension.")
            # Load from YAML
            if default.suffix in {".yaml", ".yml"}:
                default = MinyDict.from_yaml(default)
            # Load from Pickle
            elif default.suffix in {".pickle", ".pkl"}:
                default = MinyDict.from_pickle(default)
            # Load from JSON
            else:
                default = MinyDict.from_json(default)
        # `defaults` is a dictionnary: convert it to a resolved MinyDict
        elif isinstance(default, dict):
            default = MinyDict(default).resolve()
        # `defaults` is a list: recursively call load_defaults on each element
        # then sequentially merge all dictionaries to enable hierarchical defaults
        elif isinstance(default, list):
            defaults = [Parser.load_defaults(d) for d in default]
            default = MinyDict()
            for d in defaults:
                default.update(d, strict=False)

        assert isinstance(default, MinyDict)
        return default

    def _print(self, *args, **kwargs):
        if self.conf.verbose > 0:
            print(*args, **kwargs)

    def _parse_args(self):
        # check arguments syntax
        Parser.check_args(self._argv)
        # edit configuration to use the command-line special (@) arguments
        self._parse_conf()
        # create a dictionary from the command-line string arguments
        args = Parser.map_argv(
            self._argv, self.conf.allow_overwrites, self.conf.warn_overwrites
        )
        # parse the dictionary's values into known types
        args = Parser.parse_arg_types(args, self.conf.parse_env, self.conf.warn_env)

        # store the parsed & typed arguments in a MinyDict
        self.args = MinyDict(**args)

    def _parse_conf(self):
        # find all potentially overridable arguments
        special_keys = [f"@{k}" for k in self.conf.keys()]
        # find all minydra-specific command-line args:
        # they must start with an "@" AND be in special_keys
        # so that @unknown=4 will be kept as an argument, not a configuration
        # argument.
        command_line_special_keys = [
            arg for arg in self._argv if arg.split("=")[0] in special_keys
        ]
        # No special (@) arguments: nothing to do
        if len(command_line_special_keys) == 0:
            return
        # create a dictionary of special (@) arguments ({key:value})
        mapped_specials = Parser.map_argv(command_line_special_keys, False, False)
        # parse the dictionary's values into known types
        parsed_specials = Parser.parse_arg_types(mapped_specials, True, True)
        # override conf from special (@) command-line arguments
        self.conf.update({k[1:]: v for k, v in parsed_specials.items()})

    @staticmethod
    def check_args(args: List[str]) -> None:
        """
        Checks the syntax of received arguments. Only `key=value`, `positiveArg`,
        `-negativeArg` patters are allowed in `sys.argv[1:]`.

        Args:
            args (list): List of arguments from `sys.argv[1:]`

        Raises:
            MinydraWrongArgumentException: ` =` in arguments
            MinydraWrongArgumentException: `= ` in arguments
            MinydraWrongArgumentException: Command-line ends with `=`
            MinydraWrongArgumentException: Argument key starts with a `-`
        """
        args_str = " ".join(args)
        if " =" in args_str:
            raise MinydraWrongArgumentException(
                "Found space around `=` sign."
                + " Named arguments should be used as key=value"
            )
        if "= " in args_str:
            raise MinydraWrongArgumentException(
                "Found space around `=` sign."
                + " Named arguments should be used as key=value"
            )
        if args_str.endswith("="):
            raise MinydraWrongArgumentException(
                "Missing argument after `=` sign."
                + " Named arguments should be used as key=value"
            )
        for arg in args:
            if "=" in arg:
                if arg.startswith("-"):
                    raise MinydraWrongArgumentException(
                        "Cannot start a named argument with a -"
                    )
            if arg.startswith("."):
                raise MinydraWrongArgumentException("Cannot start an argument with a .")
        return

    @staticmethod
    def _force_type(value: str, type_str: str) -> Any:
        """
        Applies a type constructor to a value, e.g. `float(value)`,
        if `type_str` is in `Parser.known_types`.

        Args:
            value (str): The value to transform.
            type_str (str): The string for the type constructor,
                as per `Parser.known_args`.

        Returns:
            Any: typed value if the `type_str` is known, `value` otherwise.
        """
        if type_str == "bool":
            return bool(value)
        if type_str == "int":
            return int(float(value))
        if type_str == "float":
            return float(value)
        if type_str == "str":
            return str(value)

    @staticmethod
    def _infer_arg_type(arg: Any, type_str: Optional[str] = None) -> Any:
        """
        Parses an argument: returns it if it is not a string, else:
            * parses to int
            * parses to float
            * parses to bool
            * parses to a list
            * parses to a dict

        Type can be forced by appending `___type` to the key

        Recursive calls are applied to list and dict items

        Args:
            arg (Any): Argument to parse

        Returns:
            Any: parsed argument
        """
        if not isinstance(arg, str):
            return arg

        if type_str is not None:
            return Parser._force_type(arg, type_str)

        if arg.isdigit():
            return int(arg)

        try:
            arg = float(arg)
            return arg
        except ValueError:
            pass

        if arg.lower() == "true":
            return True

        if arg.lower() == "false":
            return False

        if arg.startswith("[") and arg.endswith("]"):
            return [Parser._infer_arg_type(v) for v in ast.literal_eval(arg)]

        if arg.startswith("{") and arg.endswith("}"):
            return {
                Parser._infer_arg_type(k): Parser._infer_arg_type(v)
                for k, v in ast.literal_eval(arg).items()
            }

        return arg

    @staticmethod
    def parse_arg_types(
        args: dict, parse_env: bool = True, warn_env: bool = True
    ) -> dict:
        """
        Automatically infer individual arguments' types

        Args:
            args (dict): dictionnary of arguments
            parse_env (bool, optional): Whether to parse environment variables.
                Defaults to True.
            warn_env (bool, optional): Whether to print a warning in case an env
                variable cannot be found. Defaults to True.

        Returns:
            dict: Args dict with inferred type values
        """
        typed = {}
        for k, v in args.items():

            if parse_env:
                v = Parser.set_env(v, warn_env)
            type_str = None
            if Parser.type_separator in k:
                candidate_k, candidate_type_str = k.split(Parser.type_separator)
                if candidate_type_str in Parser.known_types:
                    type_str = candidate_type_str
                    k = candidate_k
            typed[k] = Parser._infer_arg_type(v, type_str)
        return typed

    @staticmethod
    def set_env(value: str, warn_env: bool = True) -> str:
        """
        Replaces environment variables with their values

        Args:
            value (str): Environment variable identifier $VAR
            warn_env (bool, optional): Whether to print a warning if an env variable
                cannot be found. Defaults to True.

        Returns:
            str: Argument with resolved env variables
        """
        if not isinstance(value, str):
            return value
        arg_vars = re.findall(r"\$([\w_]+)", value)
        for arg_var in arg_vars:
            env_var = os.getenv(arg_var)
            if env_var is None and warn_env:
                Parser.warn(
                    f"Detected variable ${arg_var}"
                    + ", but could not find it in the environment. "
                    + f"Keeping raw value ${arg_var}.",
                )
            else:
                value = value.replace("$" + arg_var, env_var)

        return value

    @staticmethod
    def warn(text: str):
        """
        Print a warning as `"[Minydra Warning] " + text`

        Args:
            text (str): Warning text
        """
        text = "[Minydra Warning] " + text
        print(text)

    @staticmethod
    def map_argv(args, allow_overwrites, warn_overwrites):
        """
        Create a dictionnary from the list of arguments:

            * `key=value` -> `{key: value}`
            * `key`       -> `{key: True}`
            * `-key`      -> `{key: False}`

        Args:
            args (list): List of arguments to map into a dictionnary
            allow_overwrites (bool): Whether repeating arguments are allowed. If True,
            the last value is kept
            warn_overwrites (bool): Whether to print a warning in case an argument
                is repeated (and it is allowed)

        Raises:
            MinydraWrongArgumentException: An argument is repeated and allow_overwrites
                is False

        Returns:
            dict: Mapped arguments
        """
        args_dict = {}
        for arg in args:
            if "=" in arg:
                values = arg.split("=")
                key = values[0]
                value = "=".join(values[1:])
                key = key.strip()
                value = value.strip()
            elif arg.startswith("-"):
                key = arg[1:].strip()
                value = False
            else:
                key = arg.strip()
                value = True

            if key in args_dict:
                if not allow_overwrites:
                    raise MinydraWrongArgumentException(
                        f"Repeated argument {key} with `allow_overwrites=False`"
                    )
                if warn_overwrites:
                    text = f"Repeated argument {key}," + " overwriting previous value."
                    Parser.warn(text)

            args_dict[key] = value

        return args_dict
