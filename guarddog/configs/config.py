import importlib
from abc import ABC, abstractmethod
from collections.abc import Iterator, Iterable
from dataclasses import dataclass
from os import PathLike
from typing import Type

import yaml

from guarddog.analyzer.metadata.detector import Detector


class ConfigError(Exception):
    pass


@dataclass(kw_only=True, frozen=True)
class HeuristicConfig(ABC):
    key: str
    category: str
    description: str
    disabled: bool
    location: str

    @abstractmethod
    def join(self, *configs: 'HeuristicConfig') -> 'HeuristicConfig':
        pass


class SourcecodeConfig(HeuristicConfig):
    def join(self, *configs: 'SourcecodeConfig') -> 'SourcecodeConfig':
        def get_first(keyword):
            for config in [self, *configs]:
                if config and config.__dict__[keyword]:
                    return config.__dict__[keyword]

        return (
            SourcecodeConfig(
                key=get_first("key"),
                description=get_first("description"),
                category=get_first("category"),
                disabled=get_first("disabled"),
                location=get_first("location")
            )
        )


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

    def join(self, *configs: 'MetadataConfig') -> 'MetadataConfig':
        def get_first(keyword):
            for config in [self, *configs]:
                if config and config.__dict__[keyword]:
                    return config.__dict__[keyword]

        return (
            MetadataConfig(
                key=get_first("key"),
                description=get_first("description"),
                category=get_first("category"),
                disabled=get_first("disabled"),
                location=get_first("location")
            )
        )


class ConfigFile:
    def __init__(self, file: PathLike[str]):
        try:
            with open(file, 'r') as file:
                self._contents = yaml.safe_load(file)
        except FileNotFoundError:
            raise ConfigError()

    def get_metadata(self) -> Iterator[MetadataConfig]:
        for key, item in self._contents.get("metadata", {}).items():
            yield (
                MetadataConfig(
                    key=key,
                    category=item.get("category"),
                    description=item.get("description"),
                    disabled=item.get("disabled"),
                    location=item.get("location")
                )
            )

    def get_sourcecode(self) -> Iterator[SourcecodeConfig]:
        for key, item in self._contents.get("sourcecode", {}).items():
            yield (
                SourcecodeConfig(
                    key=key,
                    category=item.get("category"),
                    description=item.get("description"),
                    disabled=item.get("disabled"),
                    location=item.get("location")
                )
            )


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
        self._metadata[metadata.key] = metadata.join(existing_metadata)

    def add_sourcecode(self, sourcecode: SourcecodeConfig):
        if sourcecode.key in self._metadata:
            raise ConfigError("Sourcecode Heuristic '%s' has a key that conflicts with a Metadata Heuristic")

        existing_sourcecode = self._sourcecode.get(sourcecode.key)
        self._sourcecode[sourcecode.key] = sourcecode.join(existing_sourcecode)

    def get_metadata(self) -> Iterable[MetadataConfig]:
        return list(self._metadata.values())

    def get_sourcecode(self) -> Iterable[SourcecodeConfig]:
        return list(self._sourcecode.values())
