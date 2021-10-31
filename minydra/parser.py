import ast
import os
import re
import sys

from minydra.console import MinyConsole
from minydra.dict import MinyDict
from minydra.exceptions import MinydraWrongArgumentException


class Parser:

    known_types = {
        "bool",
        "int",
        "float",
        # "dict",
        # "list",
        "str",
        # "set",
    }

    type_separator = "___"

    def __init__(
        self,
        verbose=0,
        allow_overwrites=False,
        warn_overwrites=True,
        parse_env=True,
        warn_env=True,
    ) -> None:
        """
        Create a Minydra Parser to parse arbitrary commandline argument as key=value

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
        """
        super().__init__()

        self.verbose = verbose
        self.allow_overwrites = allow_overwrites
        self.warn_overwrites = warn_overwrites
        self.parse_env = parse_env
        self.warn_env = warn_env
        self.console = MinyConsole()

        self._argv = sys.argv[1:]
        self._print("sys.argv:", self._argv)

        self._parse_args()

    def _print(self, *args, **kwargs):
        if self.verbose > 0:
            print(*args, **kwargs)

    def _parse_args(self):
        self.dict_args = Parser.parse_args(
            self._argv,
            self.allow_overwrites,
            self.warn_overwrites,
            self.parse_env,
            self.warn_env,
            self.console,
        )
        self.args = MinyDict(**self.dict_args)

    @staticmethod
    def parse_args(
        args,
        allow_overwrites=True,
        warn_overwrites=True,
        parse_env=True,
        warn_env=True,
        console=None,
    ):
        Parser.check_args(args)
        args = Parser.map_args(args, allow_overwrites, warn_overwrites, console)
        args = Parser.sanitize_args(args, parse_env, warn_env, console)
        return args

    @staticmethod
    def check_args(args):
        """
        Checks the syntax of received arguments

        Args:
            args (list): List of arguments from sys.argv[1:]

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
    def _force_type(value, type_str):

        if type_str == "bool":
            return bool(value)
        if type_str == "int":
            return int(float(value))
        if type_str == "float":
            return float(value)
        if type_str == "str":
            return str(value)

    @staticmethod
    def _parse_arg(arg, type_str=None):
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
            return [Parser._parse_arg(v) for v in ast.literal_eval(arg)]

        if arg.startswith("{") and arg.endswith("}"):
            return {
                Parser._parse_arg(k): Parser._parse_arg(v)
                for k, v in ast.literal_eval(arg).items()
            }

        return arg

    @staticmethod
    def sanitize_args(args, parse_env=True, warn_env=True, console: MinyConsole = None):
        """
        Automatically infer individual arguments' types

        Args:
            args (dict): dictionnary of arguments
            parse_env (bool, optional): Whether to parse environment variables.
                Defaults to True.
            warn_env (bool, optional): Whether to print a warning in case an env
                variable cannot be found. Defaults to True.
            console (MinyConsole, optional): Console to print the warning.
                Defaults to None.

        Returns:
            dict: Sanitized dict
        """
        sane = {}
        for k, v in args.items():

            if parse_env:
                v = Parser.set_env(v, warn_env, console)
            type_str = None
            if Parser.type_separator in k:
                candidate_k, candidate_type_str = k.split(Parser.type_separator)
                if candidate_type_str in Parser.known_types:
                    type_str = candidate_type_str
                    k = candidate_k
            sane[k] = Parser._parse_arg(v, type_str)
        return sane

    @staticmethod
    def set_env(value: str, warn_env: bool = True, console: MinyConsole = None) -> str:
        """
        Replaces environment variables with their values

        Args:
            value (str): Environment variable identifier $VAR
            warn_env (bool, optional): Whether to print a warning if an env variable
                cannot be found. Defaults to True.
            console (MinyConsole, optional): Console to print the warning.
                Defaults to None.

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
                    console,
                )
            else:
                value = value.replace("$" + arg_var, env_var)

        return value

    @staticmethod
    def warn(text: str, console: MinyConsole = None):
        """
        Print a warning using a Console or standard print()

        Args:
            text (str): Warning text
            console (MinyConsole, optional): Console to print the warning.
                Defaults to None.
        """
        text = "[Minydra Warning] " + text
        if console is not None:
            print(console.warn(text))
        else:
            print(text)

    @staticmethod
    def map_args(args, allow_overwrites, warn_overwrites, console: MinyConsole = None):
        """
        Create a dictionnary from the list of arguments:
        key=value -> {key: value}
        key       -> {key: True}
        -key      -> {key: False}

        Args:
            args (list): List of arguments to map into a dictionnary
            allow_overwrites (bool): Whether repeating arguments are allowed. If True,
            the last value is kept
            warn_overwrites (bool): Whether to print a warning in case an argument
                is repeated (and it is allowed)
            console (MinyConsole, optional): Console to print warnings.
                Defaults to None.

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
                    Parser.warn(text, console)

            args_dict[key] = value

        return args_dict
