from __future__ import annotations

import contextlib
import dataclasses
import inspect
from collections.abc import Callable, Generator, Mapping, Sequence
from typing import Any, Self


@dataclasses.dataclass(frozen=True)
class MockedCall:
    args: Sequence[Any]
    kwargs: Mapping[str, Any]


class ExpectorMixin:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._expectations: list[Any] | None = None
        self._calls: list[MockedCall] = []

        for name, value in inspect.getmembers(self):
            if not hasattr(value, "_expectation_builder"):
                continue
            setattr(self, name.removeprefix("_"), value)

    @property
    def calls(self) -> Sequence[MockedCall]:
        return self._calls

    @property
    def on(self) -> ExpectationBuilders:
        return ExpectationBuilders(self)

    @contextlib.contextmanager
    def expect(self, *expectations: Any) -> Generator[None]:
        self._expectations = list(expectations)
        yield
        if self._expectations:
            raise AssertionError(f"Expectations were not used: {self._expectations}")
        self._expectations = None


def mocked[T](mocked_impl: Callable[..., T]) -> Callable[..., T]:
    if mocked_impl.__name__.startswith("_"):
        mocked_name = mocked_impl.__name__.removeprefix("_")
    else:
        raise RuntimeError("Mocked function should start with an underscore")

    expectation_attrs, mocked_sig = _extract_mock_args(mocked_impl)

    def wrapped(self: ExpectorMixin, *args: Any, **kwargs: Any) -> T:
        if self._expectations is None:
            raise AssertionError("Mocked function called without expectations")
        if not self._expectations:
            raise AssertionError("Ran out of expectations!")

        expectation = self._expectations.pop(0)
        if expectation.name != mocked_name:
            raise AssertionError(f"Expected mock for '{mocked_name}', got: '{expectation.name}'")

        self._calls.append(MockedCall(args=args, kwargs=kwargs))

        expected_args = expectation.input_args
        actual_args = mocked_sig.bind(*args, **kwargs)
        if not _do_args_match(expected=expected_args, actual=actual_args):
            raise AssertionError(f"Args did not match\nExpected: {expected_args}\nGot: {actual_args}")

        kwargs = kwargs | {f"MOCK_{name}": expectation.attrs[name] for name in expectation_attrs}
        return mocked_impl(self, *args, **kwargs)

    wrapped._expectation_builder = ExpectationBuilder(  # type: ignore[attr-defined]
        name=mocked_name,
        sig=mocked_sig,
        attrs={name: param.default for name, param in expectation_attrs.items()},
    )

    return wrapped


class ExpectationBuilders:
    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def __getattr__(self, name: str) -> Callable[..., Expectation]:
        mocked_func = getattr(self._obj, f"_{name}", None)
        if mocked_func is None:
            raise AttributeError(f"{name} is not a mocked function")

        builder = getattr(mocked_func, "_expectation_builder", None)
        if builder is None:
            raise AttributeError(f"{name} is not a mocked function")

        assert isinstance(builder, ExpectationBuilder)
        return builder


@dataclasses.dataclass(frozen=True)
class ExpectationBuilder:
    name: str
    sig: inspect.Signature
    attrs: Mapping[str, Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Expectation:
        return Expectation(
            name=self.name,
            input_args=self.sig.bind(*args, **kwargs),
            attrs=self.attrs,
        )


@dataclasses.dataclass(frozen=True)
class Expectation:
    name: str
    input_args: inspect.BoundArguments
    attrs: Mapping[str, Any]

    def __getattr__(self, name: str) -> Callable[[Any], Self]:
        if name not in self.attrs:
            raise AttributeError(f"Unknown attribute: {name}")
        return lambda v: dataclasses.replace(self, attrs={**self.attrs, name: v})


def _extract_mock_args(mocked_impl: Callable[..., Any]) -> tuple[Mapping[str, inspect.Parameter], inspect.Signature]:
    mocked_sig = inspect.signature(mocked_impl, eval_str=True)
    expectation_attrs = {}

    input_params = []
    for param in mocked_sig.parameters.values():
        if param.name == "self":
            pass
        elif param.name.startswith("MOCK_"):
            expectation_attrs[param.name.removeprefix("MOCK_")] = param
        else:
            input_params.append(param)

    mocked_sig = mocked_sig.replace(parameters=input_params)

    return expectation_attrs, mocked_sig


def _do_args_match(*, expected: inspect.BoundArguments, actual: inspect.BoundArguments) -> bool:
    for expected_arg, actual_arg in zip(expected.args, actual.args, strict=True):
        if isinstance(expected_arg, list) and Ellipsis in expected_arg:
            for i, arg in enumerate(expected_arg):
                if arg is Ellipsis:
                    break
                elif i >= len(actual_arg) or arg != actual_arg[i]:
                    return False
        elif expected_arg != actual_arg:
            return False

    if expected.kwargs != actual.kwargs:  # noqa: SIM103
        return False

    return True
