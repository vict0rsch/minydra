# Examples 🦎

This folder contains a set of examples showcasing how to use `minydra`.

## Simple usage

Use minydra with a Parser object, a decorator or a provided utility function. All 3 methods accept the parser's [init args](https://github.com/vict0rsch/minydra#getting-started)

Code: [**`parser.py`**](parser.py)

```python
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
```

Code: [**`decorator.py`**](decorator.py)

```python
import minydra


@minydra.parse_args(verbose=0, allow_overwrites=False)
def main(args):
    args.resolve().pretty_print()


if __name__ == "__main__":
    main()
```

Code: [**`resolved_args.py`**](resolved_args.py)

```python
from minydra import resolved_args

if __name__ == "__main__":

    args = resolved_args()
    args.pretty_print()
```

Commands:

```bash
python decorator.py outdir=$HOME/project save -log learning_rate=1e-4 batch_size=64
python parser.py outdir=$HOME/project save -log learning_rate=1e-4 batch_size=64
python resolved_args.py outdir=$HOME/project save -log learning_rate=1e-4 batch_size=64
```

Same output:

```text
╭───────────────────────────────────────────╮
│ batch_size    : 64                        │
│ learning_rate : 0.0001                    │
│ log           : False                     │
│ outdir        : /Users/victor/project     │
│ save          : True                      │
╰───────────────────────────────────────────╯
```

## Configuration-based Demo

This example showcases a complete "miny-workflow":

1. parse arbitrary args
2. load a configuration file
3. update that configuration with the command-line args
    * Optionally [prevent typos with `strict` mode](#strict-mode)
4. freeze the args so no later piece of code alters them
5. pretty-prints them for user-friendliness
6. saves resulting config to a file, illustrating dot-accessible nested (miny) dicts

Code: [**`demo.py`**](demo.py)

```python
from pathlib import Path

from minydra import MinyDict, resolved_args

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
```

Config: [**`demo.json`**](demo.json)

```json
{
    "log": {
        "outdir": "/some/path",
        "project": "demo",
        "logger": {
            "log_level": "DEBUG",
            "logger_name": "minydra"
        }
    },
    "verbose": false
}
```

You can also load a `yaml` config with `to/from_yaml` **provided** you have either installed `minydra` with the `yaml` extra dependency (`pip install minydra[yaml]`) or installed `PyYAML` manually.

Config: [**`demo.yaml`**](demo.yaml)

```yaml
# Example yaml conf. YAML requires an extra dependency, PyYAML:
#
# $ pip install minydra[yaml]
#
log: # logging configuration
  outdir: /some/path # where to store execution results
  project: demo # project name
  logger: # python' logging.logger params
    log_level: DEBUG # logger's log level
    logger_name: minydra # logger's name
verbose: false # code verbose level
```

`MinyDicts` can also be loaded/dumped as plain Python objects with `to/from_pickle`.

## Dumping & Loading

Code: [**`dumps.py`**](dumps.py)


```python
from pathlib import Path

from minydra import resolved_args

if __name__ == "__main__":
    args = resolved_args()

    format = args.format or "json"

    args.pretty_print()

    # notice the to_X() methods return the path to the created file:

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
```

Command

```bash
python examples/dumps.py path="./myargs.pkl" format=pickle cleanup
python examples/dumps.py path="./myargs.yaml" format=yaml cleanup
python examples/dumps.py path="./myargs.json" format=json cleanup
```

Output (almost identical, except for the paths/formats):

```text
╭────────────────────────────╮
│ cleanup : True             │
│ format  : pickle           │
│ path    : ./myargs.pkl     │
╰────────────────────────────╯
Dumped args to /Users/victor/Documents/Github/vict0rsch/minydra/myargs.pkl
Cleaning up
```

## Strict mode

To prevent typos from the command-line, the `MinyDict.update` method has a strict mode: updating a `MinyDict` with another one using `strict=True` will raise a `KeyError` if the key does not already exist in the target dict.

Code: [**`strict.py`**](strict.py)


```python
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
        args = MinyDict.from_json(path).update(args, strict=True) # <<< strict mode

    args.pretty_print()
```

No typo:

```text
$ python examples/strict.py default=./examples/demo.json log.logger.log_level=INFO
╭──────────────────────────────╮
│ log                          │
│ │logger                      │
│ │ │log_level   : INFO        │
│ │ │logger_name : minydra     │
│ │outdir  : /some/path        │
│ │project : demo              │
│ verbose : False              │
╰──────────────────────────────╯
```

Typo:

```text
$ python examples/strict.py default=./examples/demo.json log.logger.log_leveel=INFO
Traceback (most recent call last):
  File "/Users/victor/Documents/Github/vict0rsch/minydra/examples/strict.py", line 13, in <module>
    args = MinyDict.from_json(path).update(args, strict=True)
  File "/Users/victor/Documents/Github/vict0rsch/minydra/minydra/dict.py", line 111, in update
    self[k].update(v, strict=strict)
  File "/Users/victor/Documents/Github/vict0rsch/minydra/minydra/dict.py", line 111, in update
    self[k].update(v, strict=strict)
  File "/Users/victor/Documents/Github/vict0rsch/minydra/minydra/dict.py", line 100, in update
    raise KeyError(
KeyError: 'Cannot create a non-existing key in strict mode ({"log_leveel":INFO}).'
```

In general:

```python
In [1]: from minydra import MinyDict

In [2]: d = MinyDict({"a": 1, "b": {"c": 3}}).pretty_print()
╭────────────╮
│ a : 1      │
│ b          │
│ │c : 3     │
╰────────────╯

In [3]: d.update({"a": 10}, strict=True).pretty_print() # update existing key
╭────────────╮
│ a : 10     │
│ b          │
│ │c : 3     │
╰────────────╯
Out[3]: {'a': 10, 'b': {'c': 3}}

In [4]: d.update({"b": {"c": 0}}, strict=True).pretty_print() # update existing nested key
╭────────────╮
│ a : 10     │
│ b          │
│ │c : 0     │
╰────────────╯
Out[4]: {'a': 10, 'b': {'c': 0}}

In [5]: d.update({"b": {"e": 2}}, strict=True).pretty_print() # create new key: not allowed in strict mode
...
KeyError: 'Cannot create a non-existing key in strict mode ({"e":2}).'

In [6]: d.update({"b": {"e": 2}}).pretty_print() # default is strict=False, allowing for new keys
╭────────────╮
│ a : 10     │
│ b          │
│ │c : 0     │
│ │e : 2     │
╰────────────╯
Out[6]: {'a': 10, 'b': {'c': 0, 'e': 2}}
```

## Protected attributes

`MinyDict`'s methods (including the `dict` class's) are protected, they are read-only and you cannot therefore set _attributes_ with there names, like `args.get = 2`. If you do need to have a `get` argument, you can access it through _items_: `args["get"] = 2`.

Code: [**`protected.py`**](protected.py):

```python
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
```

```text
python examples/protected.py server.conf.port=8000 get=3
╭────────────────────╮
│ get    : 3         │
│ server             │
│ │conf              │
│ │ │port : 8000     │
╰────────────────────╯
<built-in method get of MinyDict object at 0x100ccd4a0>
3
dict_items([('get', 3), ('server', {'conf': {'port': 8000}})])
{'conf': {'port': 8000}}
```

```python
In [1]: from minydra import MinyDict

In [2]: d = MinyDict()

In [3]: d.get = 3
...
AttributeError: `get` is a  protected attribute of MinyDict.

In [4]: d["get"] = 3

In [5]: d["get"]
Out[5]: 3

In [6]: d.get
Out[6]: <function MinyDict.get(key, default=None, /)>

In [7]: protected = dir(MinyDict)

In [8]: print("Protected attributes:\n  " + '\n  '.join(protected))
Protected attributes:
  __class__
  __class_getitem__
  __contains__
  __deepcopy__
  __delattr__
  __delitem__
  __dict__
  __dir__
  __doc__
  __eq__
  __format__
  __ge__
  __getattr__
  __getattribute__
  __getitem__
  __getnewargs__
  __getstate__
  __gt__
  __hash__
  __init__
  __init_subclass__
  __ior__
  __iter__
  __le__
  __len__
  __lt__
  __module__
  __ne__
  __new__
  __or__
  __reduce__
  __reduce_ex__
  __repr__
  __reversed__
  __ror__
  __setattr__
  __setitem__
  __setstate__
  __sizeof__
  __str__
  __subclasshook__
  __weakref__
  _frozen
  _hook
  _pretty_print_rec
  _resolve_dots
  _resolve_nests
  clear
  copy
  deepcopy
  freeze
  from_json
  from_pickle
  from_yaml
  fromkeys
  get
  items
  keys
  pop
  popitem
  pretty_print
  resolve
  setdefault
  to_dict
  to_json
  to_pickle
  to_yaml
  unfreeze
  update
  values
```
