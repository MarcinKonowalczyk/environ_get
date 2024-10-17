# environ_get

[![Single file](https://img.shields.io/badge/single%20file%20-%20purple)](https://raw.githubusercontent.com/MarcinKonowalczyk/enviton_get/main/src/enviton_get/enviton_get.py)
[![test](https://github.com/MarcinKonowalczyk/enviton_get/actions/workflows/test.yml/badge.svg)](https://github.com/MarcinKonowalczyk/enviton_get/actions/workflows/test.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
![Python versions](https://img.shields.io/badge/python-3.9%20~%203.13-blue)

Single-file module with a utility function to get the value of the key from the environment
with optional type conversion and default value.

Tested in Python 3.9+.

# Usage

```python
>>> from environ_get import environ_get
>>> FOO = environ_get("FOO", default="bar")
>>> FOO
'bar'
>>> import os
>>> os.environ["FOO"] = "baz"
>>> FOO = environ_get("FOO", default="bar")
>>> FOO
'baz'
```

Or with type conversion:

```python
>>> environ_get("FOO", default=123, type=int)
123
>>> import os
>>> os.environ["FOO"] = "6768"
>>> environ_get("FOO", default=123, type=int)
6768
```

## Install

Just copy the single-module file to your project and import it.

```bash
cp ./src/environ_get/environ_get.py src/your_package/_environ_get.py
```

Or even better, without checking out the repository:

```bash
curl https://raw.githubusercontent.com/MarcinKonowalczyk/environ_get/main/src/environ_get/environ_get.py > src/your_package/_environ_get.py
```

Note that like this *you take ownership of the code* and you are responsible for keeping it up-to-date. If you change it that's fine (keep the license pls). That's the point here. You can also copy the code to your project and modify it as you wish.

If you want you can also build and install it as a package, but then the source lives somewhere else. That might be what you want though. 🤷‍♀️

```bash
pip install flit
flit build
ls dist/*
pip install dist/*.whl
```
