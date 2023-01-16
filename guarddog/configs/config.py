from collections.abc import Iterator, Iterable
from os import PathLike
from pathlib import Path
from typing import Type, TypeVar

import yaml

from guarddog.configs.heuristic_config import HeuristicConfig, MetadataConfig, SourcecodeConfig
from guarddog.utils.exceptions import ConfigError
from guarddog.utils.filters import filter_by_attributes

_HeuristicConfig_T = TypeVar("_HeuristicConfig_T", bound=HeuristicConfig)


class ConfigFile:
    def __init__(self, location: PathLike[str]):
        try:
            self._location = Path(location).absolute()
            with open(location, 'r') as file:
                self._contents = yaml.safe_load(file)
        except FileNotFoundError:
            raise ConfigError()

    def _get_heuristic(self, cls: Type[_HeuristicConfig_T]) -> Iterator[_HeuristicConfig_T]:
        all_configs = self._contents.get(cls.class_key(), {}).items()

        for heuristic_key, config in all_configs:
            kwargs = {
                slot: config.get(slot)

                for slot in cls.__slots__
            }

            kwargs["key"] = heuristic_key
            kwargs["config_location"] = self._location

            yield cls(**kwargs)

    def get_metadata(self) -> Iterator[MetadataConfig]:
        return self._get_heuristic(MetadataConfig)

    def get_sourcecode(self) -> Iterator[SourcecodeConfig]:
        return self._get_heuristic(SourcecodeConfig)


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

        try:
            existing_metadata = self._metadata[metadata.key]
        except KeyError:
            new_metadata = metadata
        else:
            new_metadata = existing_metadata.replace(**metadata.as_dict())

        self._metadata[metadata.key] = new_metadata

    def add_sourcecode(self, sourcecode: SourcecodeConfig):
        if sourcecode.key in self._metadata:
            raise ConfigError("Sourcecode Heuristic '%s' has a key that conflicts with a Metadata Heuristic")

        try:
            existing_sourcecode = self._sourcecode[sourcecode.key]
        except KeyError:
            new_sourcecode = sourcecode
        else:
            new_sourcecode = existing_sourcecode.replace(**sourcecode.as_dict())

        self._sourcecode[sourcecode.key] = new_sourcecode

    def get_metadata(self, **filters) -> Iterable[MetadataConfig]:
        return list(filter_by_attributes(self._metadata.values(), **filters))

    def get_sourcecode(self, **filters) -> Iterable[SourcecodeConfig]:
        return list(filter_by_attributes(self._sourcecode.values(), **filters))
