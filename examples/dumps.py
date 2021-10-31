from pathlib import Path

from minydra import resolved_args

if __name__ == "__main__":
    args = resolved_args()

    format = args.format or "json"

    args.pretty_print()

    if format == "json":
        dumped = Path(args.to_json(args.path or "./args.json"))
    elif format == "pickle":
        dumped = Path(args.to_pickle(args.path or "./args.pkl"))
    elif format == "yaml":
        dumped = Path(args.to_yaml(args.path or "./args.yaml"))

    print(f"Dumped args to {dumped}")

    if args.cleanup:
        print("Cleaning up")
        dumped.unlink()
    else:
        print("No cleanup")
