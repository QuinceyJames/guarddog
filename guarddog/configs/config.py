import importlib
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Type

import yaml

from guarddog.analyzer.metadata.detector import Detector


class ConfigError(Exception):
    pass


@dataclass(kw_only=True, frozen=True)
class HeuristicConfig(ABC):
    key: str
    name: str
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
                name=get_first("name"),
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
                name=get_first("name"),
                description=get_first("description"),
                category=get_first("category"),
                disabled=get_first("disabled"),
                location=get_first("location")
            )
        )


class ConfigFile:
    def __init__(self, file: str):
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
                    name=item.get("name"),
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
                    name=item.get("name"),
                    category=item.get("category"),
                    description=item.get("description"),
                    disabled=item.get("disabled"),
                    location=item.get("location")
                )
            )


class Config:
    _metadata: dict[str, MetadataConfig] = {}
    _sourcecode: dict[str, SourcecodeConfig] = {}

    def add_config(self, path: str):
        config_file = ConfigFile(path)

        for metadata in config_file.get_metadata():
            existing_metadata = self._metadata.get(metadata.key)
            self._metadata[metadata.key] = metadata.join(existing_metadata)

        for sourcecode in config_file.get_sourcecode():
            existing_sourcecode = self._sourcecode.get(sourcecode.key)
            self._sourcecode[sourcecode.key] = sourcecode.join(existing_sourcecode)

        return self

    @property
    def metadata(self) -> Iterator[MetadataConfig]:
        return iter(self._metadata.values())

    @property
    def sourcecode(self) -> Iterator[SourcecodeConfig]:
        return iter(self._sourcecode.values())
