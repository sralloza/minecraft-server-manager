"""Files manager."""

import logging
import os
from pathlib import Path
import re
from typing import Optional, Type, Union

from .exceptions import InvalidFileError

logger = logging.getLogger(__name__)
DataFile = Type["File"]


class MetaFile(type):  # pylint: disable=missing-param-doc, missing-type-doc
    """Metaclass to store different file types and its istances."""

    def __init__(cls, name, bases, attrs, **kwargs):
        type.__init__(cls, name, bases, attrs, **kwargs)

        if not bases:
            cls.subtypes = {}
            cls.memory = {}
        else:
            bases[0].subtypes[name.lower().replace("file", "")] = cls
            bases[0].memory[name.lower().replace("file", "")] = list()

    def __call__(cls, *args, **kwargs):
        instance = type.__call__(cls, *args, **kwargs)
        if not instance:
            return instance

        classname = instance.__class__.__name__.lower().replace("file", "")

        if instance not in cls.memory[classname]:
            cls.memory[classname].append(instance)

        return instance


class File(metaclass=MetaFile):
    """Representation of a file containing player data.

    Arguments:
        path (str): actual path of the File.
    """

    uuid_pattern = re.compile(
        r"([0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}"
        r"\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})\.\w+(?<!_old)$"
    )

    # For hinting purposes only (it is declared inside `MetaFile`)
    subtypes = {}
    memory = {}

    def __new__(cls, path: str):
        if cls == File:
            return File.identify(path)

        self = super().__new__(cls)
        self.__init__(path)

        return self

    def __init__(self, path: str):
        self.path = Path(path)

    def __eq__(self, other: DataFile):
        return self.path == other.path

    def __repr__(self):
        return f"{type(self).__name__}({self.as_posix()!r})"

    @property
    def uuid(self) -> str:
        """Returns the uuid of the player which data is in the file.

        Raises:
            InvalidFileError: if no uuid is found in the filename.

        Returns:
            str: uuid.
        """

        uuid = self.get_uuid_from_filepath(self.path)
        if not uuid:
            raise InvalidFileError(f"{self.path} does not contain a uuid")
        return uuid

    @classmethod
    def get_uuid_from_filepath(cls, filepath: Union[str, Path]) -> Optional[str]:
        """Returns the uuid given the filepath.

        Args:
            filepath (Union[str, Path]): filepath.

        Returns:
            Optional[str]: the uuid if success, None otherwise.
        """

        filepath = Path(filepath)

        try:
            return cls.uuid_pattern.search(filepath.as_posix()).group(1)
        except AttributeError:
            return None

    def read_bytes(self) -> bytes:
        """Returns the file content in bytes.

        Returns:
            bytes: file content.
        """

        return self.path.read_bytes()

    def remove(self):
        """Removes the actual file from the file system."""

        self.path.unlink()

    def as_posix(self) -> str:
        """Returns its file path.

        Returns:
            str: file path.
        """

        return self.path.as_posix()

    def change_uuid(self, uuid: str) -> bool:
        """Changes the uuid of the player data file.

        Args:
            uuid (str): new uuid.

        Returns:
            bool: True if the conversion was success, False otherwise.
        """

        logger.debug("Changing uuid to %s of file %s", uuid, self.path.as_posix())
        new_path = self.path.with_name(uuid + self.path.suffix)
        self.path.rename(new_path)
        self.path = new_path
        return True

    @classmethod
    def identify(cls, path: Union[str, Path]) -> Optional[DataFile]:
        """Identifies the type of player data that `path` stores.

        Args:
            path (Union[str, Path]): path of the player data file.

        Returns:
            Optional[DataFile]: If the file is identified, the a Player object is returned.
                If the file is not identified, None is returned.
        """

        path = Path(path).as_posix()
        for subtype in cls.subtypes:
            if subtype in path:
                return cls.subtypes[subtype](path)

        # TODO: raise exception if file is not identified
        return None

    @classmethod
    def gen_files(cls, path: Path):
        """Scans dir `path` recursively looking for files that contain minecraft player data.

        Args:
            path (Path): root dir to start recursive scan.
        """

        logger.debug("generating files for path %s", path.as_posix())
        for root, _, files in os.walk(path):
            for filename in files:
                file = Path(root).joinpath(filename)
                uuid = cls.get_uuid_from_filepath(file)

                if uuid:
                    File.identify(file)
        logger.info("files generated")


class PlayerDataFile(File):
    """Stores the player's inventory and ender chest, as well as other stats,
    like health, hunger, etc.

    """


class StatsFile(File):
    """Stores player's statistics."""


class AdvancementsFile(File):
    """Stores players advancements."""
