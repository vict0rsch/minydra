import minydra


@minydra.parse_args(verbose=0, allow_overwrites=False)
def main(args):
    args.resolve().pretty_print()


if __name__ == "__main__":
    main()
