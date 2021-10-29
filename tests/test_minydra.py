import minydra
import sys
from unittest.mock import patch


def test_resolved_args():
    with patch.object(sys, "argv", ["", "foo=bar", "-verbose"]):
        args = minydra.resolved_args()
        assert not args.verbose
        assert args.foo == "bar"


def test_parse_args_decorator():
    with patch.object(sys, "argv", ["", "foo=bar", "-verbose"]):

        @minydra.parse_args()
        def main(args):
            args.resolve()
            assert args.verbose is False
            assert args.foo == "bar"

        main()
