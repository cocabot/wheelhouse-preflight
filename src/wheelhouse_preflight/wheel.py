"""Read bounded metadata from wheel archives without extracting or importing them."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import struct
import zipfile
import zlib
from dataclasses import dataclass
from email import policy
from email.parser import Parser
from pathlib import Path
from typing import BinaryIO

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.tags import Tag, parse_tag
from packaging.utils import (
    InvalidName,
    InvalidWheelFilename,
    canonicalize_name,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version

from .target import InputError

MAX_WHEELS = 10_000
MAX_WHEEL_BYTES = 1024 * 1024 * 1024
MAX_ZIP_MEMBERS = 50_000
MAX_CENTRAL_DIRECTORY_BYTES = 8 * 1024 * 1024
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_WHEEL_METADATA_BYTES = 64 * 1024


@dataclass(frozen=True)
class Wheel:
    path: Path
    name: str
    version: Version
    tags: frozenset[Tag]
    requires_python: SpecifierSet
    requires_dist: tuple[Requirement, ...]
    provides_extra: frozenset[str]
    sha256: str


def _bounded_tags(value: str) -> frozenset[Tag]:
    parts = value.split("-")
    if len(value) > 200 or len(parts) != 3:
        raise InputError("Invalid or oversized wheel tag.")
    combinations = 1
    for part in parts:
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", part):
            raise InputError("Invalid wheel tag component.")
        combinations *= len(part.split("."))
    if combinations > 256:
        raise InputError("Compressed wheel tag exceeds the 256-combination limit.")
    return parse_tag(value)


def _check_zip_directory(stream: BinaryIO, size: int) -> None:
    """Bound ZIP metadata before ZipFile allocates its central-directory objects."""
    stream.seek(max(0, size - 65_557))
    tail = stream.read(65_557)
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise InputError("Missing ZIP end-of-central-directory record.")
    _sig, disk, cd_disk, disk_count, count, cd_size, cd_offset, comment_size = struct.unpack_from(
        "<4s4H2LH", tail, offset
    )
    if disk or cd_disk or disk_count != count:
        raise InputError("Multi-disk ZIP archives are unsupported.")
    if count == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
        raise InputError("ZIP64 archives are unsupported by the bounded metadata reader.")
    if count > MAX_ZIP_MEMBERS or cd_size > MAX_CENTRAL_DIRECTORY_BYTES:
        raise InputError("Wheel exceeds the ZIP central-directory limits.")
    eocd_offset = max(0, size - 65_557) + offset
    if len(tail) != offset + 22 + comment_size or cd_offset + cd_size != eocd_offset:
        raise InputError("Invalid ZIP central-directory bounds or trailing data.")
    stream.seek(cd_offset)
    consumed = 0
    actual_count = 0
    while consumed < cd_size:
        header = stream.read(46)
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise InputError("Invalid ZIP central-directory entry.")
        name_size, extra_size, entry_comment_size = struct.unpack_from("<HHH", header, 28)
        variable_size = name_size + extra_size + entry_comment_size
        consumed += 46 + variable_size
        actual_count += 1
        if consumed > cd_size or actual_count > MAX_ZIP_MEMBERS:
            raise InputError("Wheel exceeds the ZIP central-directory limits.")
        stream.seek(variable_size, 1)
    if actual_count != count:
        raise InputError("ZIP member count disagrees with its directory.")
    stream.seek(0)


def _read_member(archive: zipfile.ZipFile, name: str, limit: int) -> str:
    info = archive.getinfo(name)
    if info.file_size > limit or info.flag_bits & 1:
        raise InputError(f"Oversized or encrypted metadata in {name}.")
    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise InputError("Only stored or Deflate-compressed wheel metadata is supported.")
    with archive.open(info) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise InputError(f"Metadata exceeds limit in {name}.")
    return data.decode("utf-8", errors="strict")


def read_wheel(path: Path) -> Wheel:
    """Validate the identity and dependency metadata of one wheel; hash its bytes."""
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise InputError("Wheel must be a regular file, not a symlink or special file.")
        if info.st_size > MAX_WHEEL_BYTES:
            raise InputError("Wheel exceeds the 1 GiB limit.")
        _bounded_tags("-".join(path.stem.rsplit("-", 3)[-3:]))
        name, version, _build, filename_tags = parse_wheel_filename(path.name)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_BINARY", 0)
        )
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                info.st_dev,
                info.st_ino,
            ):
                raise InputError("Wheel changed while being opened.")
            if opened.st_size > MAX_WHEEL_BYTES:
                raise InputError("Wheel exceeds the 1 GiB limit.")
            _check_zip_directory(stream, opened.st_size)
            sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                members = archive.infolist()
                if len(members) > MAX_ZIP_MEMBERS:
                    raise InputError("Wheel exceeds the ZIP member limit.")
                names = [member.filename for member in members]
                if len(set(names)) != len(names):
                    raise InputError("Wheel has duplicate ZIP member names.")
                metadata_names = [n for n in names if re.fullmatch(r"[^/]+\.dist-info/METADATA", n)]
                wheel_names = [n for n in names if re.fullmatch(r"[^/]+\.dist-info/WHEEL", n)]
                if len(metadata_names) != 1 or len(wheel_names) != 1:
                    raise InputError("Wheel must have exactly one top-level METADATA and WHEEL.")
                prefix = metadata_names[0].removesuffix("/METADATA")
                if wheel_names[0] != prefix + "/WHEEL":
                    raise InputError("METADATA and WHEEL must share a dist-info directory.")
                dist_info = prefix.removesuffix(".dist-info").rsplit("-", 1)
                if (
                    len(dist_info) != 2
                    or canonicalize_name(dist_info[0]) != name
                    or Version(dist_info[1]) != version
                ):
                    raise InputError("dist-info identity disagrees with the wheel filename.")
                metadata = Parser(policy=policy.compat32).parsestr(
                    _read_member(archive, metadata_names[0], MAX_METADATA_BYTES)
                )
                wheel_metadata = Parser(policy=policy.compat32).parsestr(
                    _read_member(archive, wheel_names[0], MAX_WHEEL_METADATA_BYTES)
                )
            finished = os.fstat(stream.fileno())
            if (finished.st_size, finished.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns):
                raise InputError("Wheel changed during its audit; audit a stable copy.")
        if metadata.defects or wheel_metadata.defects:
            raise InputError("Malformed email-style wheel metadata.")
        for key in ("Metadata-Version", "Name", "Version"):
            if len(metadata.get_all(key, [])) != 1:
                raise InputError(f"Wheel must contain exactly one {key} header.")
        # Core metadata 2.x remains backward compatible. Refuse unknown major versions.
        if str(metadata["Metadata-Version"]).split(".")[0] not in {"1", "2"}:
            raise InputError("Unsupported core metadata major version.")
        if canonicalize_name(str(metadata["Name"]), validate=True) != name:
            raise InputError("METADATA Name disagrees with the wheel filename.")
        if Version(str(metadata["Version"])) != version:
            raise InputError("METADATA Version disagrees with the wheel filename.")
        if len(metadata.get_all("Requires-Python", [])) > 1:
            raise InputError("Wheel has duplicate Requires-Python headers.")
        if metadata.get_all("Requires"):
            raise InputError("Legacy Requires metadata is unsupported; use Requires-Dist.")
        if len(wheel_metadata.get_all("Wheel-Version", [])) != 1:
            raise InputError("Wheel must contain one Wheel-Version header.")
        if str(wheel_metadata["Wheel-Version"]).split(".")[0] != "1":
            raise InputError("Unsupported Wheel-Version major version.")
        wheel_tags: set[Tag] = set()
        for value in wheel_metadata.get_all("Tag", []):
            wheel_tags.update(_bounded_tags(str(value)))
            if len(wheel_tags) > 1024:
                raise InputError("WHEEL contains more than 1024 expanded tags.")
        if wheel_tags != filename_tags:
            raise InputError("WHEEL tags disagree with the wheel filename.")
        requirements = tuple(
            Requirement(str(value)) for value in metadata.get_all("Requires-Dist", [])
        )
        extras = frozenset(
            canonicalize_name(str(value), validate=True)
            for value in metadata.get_all("Provides-Extra", [])
        )
        return Wheel(
            path,
            str(name),
            version,
            filename_tags,
            SpecifierSet(str(metadata.get("Requires-Python", ""))),
            requirements,
            extras,
            sha256,
        )
    except InputError:
        raise
    except (
        OSError,
        zipfile.BadZipFile,
        UnicodeError,
        InvalidWheelFilename,
        InvalidName,
        InvalidVersion,
        InvalidRequirement,
        InvalidSpecifier,
        ValueError,
        NotImplementedError,
        RuntimeError,
        EOFError,
        zlib.error,
    ) as exc:
        raise InputError(f"Cannot read wheel metadata: {exc}") from exc
