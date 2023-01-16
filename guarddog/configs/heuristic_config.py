import dataclasses
import importlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Type, Any

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

    def replace(self, **changes: Any) -> 'HeuristicConfig':
        return dataclasses.replace(self, **changes)

    def as_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    @abstractmethod
    def class_key(cls) -> str:
        pass


@dataclass(kw_only=True, frozen=True, slots=True)
class SourcecodeConfig(HeuristicConfig):
    @property
    def absolute_location(self) -> Path:
        return Path(os.path.dirname(self.config_location), self.location)

    @classmethod
    def class_key(cls) -> str:
        return "sourcecode"


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

    @classmethod
    def class_key(cls) -> str:
        return "metadata"
