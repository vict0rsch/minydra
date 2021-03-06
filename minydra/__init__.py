from .parser import Parser

__version__ = "0.1.2"


def parse_args(
    verbose=0,
    allow_overwrites=True,
    warn_overwrites=True,
    parse_env=True,
    warn_env=True,
):
    def decorator(function):
        def wrapper(*args, **kwargs):
            parser = Parser(
                verbose=verbose,
                allow_overwrites=allow_overwrites,
                warn_overwrites=warn_overwrites,
                parse_env=parse_env,
                warn_env=warn_env,
            )
            result = function(parser.args)
            return result

        return wrapper

    return decorator
