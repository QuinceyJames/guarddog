import importlib
from abc import ABC
from collections.abc import Iterator, Iterable
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Type, TypeVar

import yaml

from guarddog.analyzer.metadata.detector import Detector


class ConfigError(Exception):
    pass


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


_HeuristicConfig_T = TypeVar("_HeuristicConfig_T", bound=HeuristicConfig)


class ConfigFile:
    def __init__(self, location: PathLike[str]):
        try:
            self._location = Path(location).absolute()
            with open(location, 'r') as file:
                self._contents = yaml.safe_load(file)
        except FileNotFoundError:
            raise ConfigError()

    def _get_heuristic(self, cls: Type[_HeuristicConfig_T], heuristic_type_key: str) -> Iterator[_HeuristicConfig_T]:
        all_configs = self._contents.get(heuristic_type_key, {}).items()

        for heuristic_key, config in all_configs:
            kwargs = {
                slot: config.get(slot)

                for slot in cls.__slots__
            }

            kwargs["key"] = heuristic_key
            kwargs["config_location"] = self._location

            yield cls(**kwargs)

    def get_metadata(self) -> Iterator[MetadataConfig]:
        return self._get_heuristic(MetadataConfig, "metadata")

    def get_sourcecode(self) -> Iterator[SourcecodeConfig]:
        return self._get_heuristic(SourcecodeConfig, "sourcecode")


class Config:
    _metadata: dict[str, MetadataConfig] = {}
    _sourcecode: dict[str, SourcecodeConfig] = {}

    def add_config_file(self, path: PathLike[str]):
        config_file = ConfigFile(path)

        for metadata in config_file.get_metadata():
            self.add_metadata(metadata)

        for sourcecode in config_file.get_sourcecode():
            self.add_sourcecode(sourcecode)

        return self

    def add_metadata(self, metadata: MetadataConfig):
        if metadata.key in self._sourcecode:
            raise ConfigError("Metadata Heuristic '%s' has a key that conflicts with a Sourcecode Heuristic")

        existing_metadata = self._metadata.get(metadata.key)
        self._metadata[metadata.key] = MetadataConfig.join(existing_metadata, metadata)

    def add_sourcecode(self, sourcecode: SourcecodeConfig):
        if sourcecode.key in self._metadata:
            raise ConfigError("Sourcecode Heuristic '%s' has a key that conflicts with a Metadata Heuristic")

        existing_sourcecode = self._sourcecode.get(sourcecode.key)
        self._sourcecode[sourcecode.key] = SourcecodeConfig.join(existing_sourcecode, sourcecode)

    def get_metadata(self) -> Iterable[MetadataConfig]:
        return list(self._metadata.values())

    def get_sourcecode(self) -> Iterable[SourcecodeConfig]:
        return list(self._sourcecode.values())
