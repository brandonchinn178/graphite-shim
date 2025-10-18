import importlib
import inspect
import pkgutil
from collections.abc import Mapping

from graphite_shim.commands.base import Command


def get_all_commands() -> Mapping[str, Command]:
    # Import + load all graphite_shim.commands.* modules
    # https://stackoverflow.com/a/3365846/4966649
    all_submodules = (
        importlib.import_module(f"{__name__}.{module_info.name}") for module_info in pkgutil.iter_modules(__path__)
    )

    return {
        cls.__tag__: cls
        for mod in all_submodules
        for _, cls in inspect.getmembers(mod, inspect.isclass)
        if hasattr(cls, "__tag__")  # set in all Command subclasses
    }
