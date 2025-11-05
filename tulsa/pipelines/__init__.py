import importlib
import inspect
import logging
import os
import pkgutil
from abc import ABC, abstractmethod

from pydantic import BaseModel


class Pipeline(ABC):
    """
    Base class for pipelines.
    """

    @property
    @abstractmethod
    def enabled(self) -> bool: ...

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        The pipeline runs in the lower priority value first.
        """
        ...

    @abstractmethod
    async def handle_item(self, item: BaseModel) -> BaseModel | None:
        """
        Handle a single item in the item iterator.
        Return `None` to drop it.
        """
        ...


def load_all_pipelines() -> list[Pipeline]:
    """
    Automatically dynamic load all pipeplines in `folder`.
    """

    ret: list[Pipeline] = []
    for _, module_name, _ in pkgutil.iter_modules(
        [os.path.join(__path__[0])], "tulsa.pipelines."
    ):
        module = importlib.import_module(module_name)
        for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(class_obj, Pipeline)) and class_name != "Pipeline":
                try:
                    ret.append(class_obj())
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"Cannot load '{class_obj.__module__}.{class_name}' pipeline: {e}"
                    )

    return ret
