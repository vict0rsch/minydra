from minydra import MinyDict, resolved_args

if __name__ == "__main__":
    # parse arbitrary args in 1 line
    args = resolved_args()

    # override default conf
    if args.default:
        path = args.default
        # delete otherwise it will be used to update the conf which does not have
        # "default" as a key, therefore raising a KeyError in strict mode
        del args.default
        args = MinyDict.from_json(path).update(args, strict=True)

    args.pretty_print()
