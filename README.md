# pttp

[![PyPI - Version](https://img.shields.io/pypi/v/pttp.svg)](https://pypi.org/project/pttp)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pttp.svg)](https://pypi.org/project/pttp)

-----

A Python tracing profiler.

Tracing profilers trace every function call in your Python program. 

Tracing profilers in Python are fairly trivial (mostly just calling `sys.settrace()`). `pttp`'s notable feature is it calls your code, so you don't have to modify your source code.


## Installation

```console
pip install pttp
```

## Usage

```console
## Generate Python trace data
python -m pttp your_script.py
python -m pttp -m your_script

## Upload 'your_script.speedscope.json' to https://speedscope.app to view the profile.
```

## License

`pttp` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
