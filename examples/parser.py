from minydra.parser import Parser

if __name__ == "__main__":
    parser = Parser(
        verbose=0,
        allow_overwrites=False,
        warn_overwrites=True,
        parse_env=True,
        warn_env=True,
    )
    args = parser.args.pretty_print().resolve().pretty_print()
