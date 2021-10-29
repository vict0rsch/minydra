from minydra import MinyDict, resolved_args
from pathlib import Path

if __name__ == "__main__":
    # parse arbitrary args in 1 line
    args = resolved_args()

    # override default conf
    if args.default:
        args = MinyDict.from_json(args.default).update(args)

    # protect args in the rest of the code execution
    args.freeze()

    # print the args in a nice orderly fashion
    args.pretty_print()

    # access args with dot/attribute access
    print(f'Using project "{args.log.project}" in {args.log.outdir}')

    # save configuration
    args.to_json(Path(args.log.outdir) / f"{args.log.project}.json")
