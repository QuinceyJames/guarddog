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

    def get_metadata(self, **filters) -> Iterable[MetadataConfig]:
        return list(filter_by_attributes(self._metadata.values(), **filters))

    def get_sourcecode(self, **filters) -> Iterable[SourcecodeConfig]:
        return list(filter_by_attributes(self._sourcecode.values(), **filters))
