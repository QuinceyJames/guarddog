import importlib
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Type

from guarddog.analyzer.metadata.detector import Detector
from guarddog.utils.exceptions import ConfigError


@dataclass(kw_only=True, frozen=True, slots=True)
class HeuristicConfig(ABC):
    key: str
    category: str
    description: str
    disabled: bool
    location: str
    config_location: Path

    @classmethod
    def join(cls, *configs: 'HeuristicConfig') -> 'HeuristicConfig':

        kwargs = {}
        for slot in cls.__slots__:

            kwargs[slot] = None
            for config in filter(None, configs):
                if (value := getattr(config, slot)) is not None:
                    kwargs[slot] = value

        return cls(**kwargs)


@dataclass(kw_only=True, frozen=True, slots=True)
class SourcecodeConfig(HeuristicConfig):
    pass


@dataclass(kw_only=True, frozen=True, slots=True)
class MetadataConfig(HeuristicConfig):

    @property
    def detector(self) -> Type[Detector]:
        module_name, _, class_name = self.location.rpartition(".")

        try:
            module = importlib.import_module(module_name)
            class_ = getattr(module, class_name)

            if issubclass(class_, Detector):
                return class_

        except ImportError:
            raise ConfigError("Cannot find module '%s' for '%s'" % (module_name, class_name))
        except AttributeError:
            raise ConfigError("Cannot find class '%s' inside module '%s'" % (class_name, module_name))
        else:
            raise ConfigError("Class '%s' must be a subclass of '%s'" % (self.key, Detector.__name__))
