from pathlib import Path

from minydra import resolved_args

if __name__ == "__main__":

    args = resolved_args(defaults=Path(__file__).parent / "demo.yaml")
    args.pretty_print()
