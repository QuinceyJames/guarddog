from abc import ABC
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

    def __init__(self):
        self._saved_heuristics: dict[str, HeuristicConfig] = {}

    def add_config_file(self, path: PathLike[str]):
        config_file = ConfigFile(path)

        for heuristic in config_file.get_metadata():
            self.save_heuristic(heuristic)

        for heuristic in config_file.get_metadata():
            self.save_heuristic(heuristic)

        return self

    def save_heuristic(self, heuristic: HeuristicConfig):
        try:
            existing_heuristic = self._saved_heuristics[heuristic.key]
        except KeyError:
            new_heuristic = heuristic
        else:
            new_heuristic = existing_heuristic.replace(**heuristic.as_dict())

        self._saved_heuristics[heuristic.key] = new_heuristic

    def get_heuristics(self, **filters) -> Iterable[HeuristicConfig]:
        return list(filter_by_attributes(self._saved_heuristics.values(), **filters))
