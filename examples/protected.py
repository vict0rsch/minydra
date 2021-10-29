import minydra


@minydra.parse_args()
def main(args):
    args.resolve().pretty_print()
    print(args.get)
    print(args["get"])
    print(args.items())
    print(args.server)


if __name__ == "__main__":
    main()
