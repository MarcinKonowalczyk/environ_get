import os
from collections.abc import Iterator

import pytest

from environ_get import environ_get, bool_parser


@pytest.fixture(autouse=True)
def prepare_environ() -> Iterator[None]:
    keys = {
        "NONEXISTENT_KEY": None,
        "INT_KEY": 42,
        "FLOAT_KEY": 3.14,
        "BOOL_KEY": True,
        "STR_KEY": "hello",
    }

    old_values = {key: os.environ.get(key) for key in keys}

    # Set the environment
    for key, value in keys.items():
        if value is not None:
            os.environ[key] = str(value)
        elif key in os.environ:
            del os.environ[key]

    yield

    # Restore the environment
    for key, value in old_values.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


def test_environ_get() -> None:
    assert environ_get("INT_KEY") == "42"
    assert environ_get("FLOAT_KEY") == "3.14"
    assert environ_get("BOOL_KEY") == "True"
    assert environ_get("STR_KEY") == "hello"
    assert environ_get("NONEXISTENT_KEY", default=None) is None


def test_bool_parser() -> None:
    assert environ_get("BOOL_KEY", type=bool_parser) is True

    os.environ["BOOL_KEY"] = "false"
    assert environ_get("BOOL_KEY", type=bool_parser) is False

    os.environ["BOOL_KEY"] = "0"
    assert environ_get("BOOL_KEY", type=bool_parser) is False

    os.environ["BOOL_KEY"] = "1"
    assert environ_get("BOOL_KEY", type=bool_parser) is True

    os.environ["BOOL_KEY"] = "true"
    assert environ_get("BOOL_KEY", type=bool_parser) is True
