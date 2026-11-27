#!/usr/bin/env python3
"""Read-only, revision-pinned importer for awesome-selfhosted-data."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import yaml


DATA_REPOSITORY = "awesome-selfhosted/awesome-selfhosted-data"
DATA_LICENSE = "CC-BY-SA-3.0"
DATA_LICENSE_URL = "https://github.com/awesome-selfhosted/awesome-selfhosted-data/blob/master/LICENSE"
ATTRIBUTION = "awesome-selfhosted contributors"
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_UNPACKED_BYTES = 128 * 1024 * 1024
MAX_FILES = 10000
MAX_RECORD_BYTES = 256 * 1024
MAX_TEXT_LENGTH = 12000
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class CatalogError(Exception):
    """Raised when an upstream snapshot is invalid or unsafe to import."""


def validate_revision(revision: str) -> str:
    if not isinstance(revision, str) or not REVISION_PATTERN.fullmatch(revision):
        raise CatalogError("revision must be a full 40-character lowercase Git commit SHA")
    return revision


def _request(url: str, *, max_bytes: int, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SYMBIOTYC-Ecosystem-Registry/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CatalogError(f"upstream request failed: {type(exc).__name__}") from exc
    if len(data) > max_bytes:
        raise CatalogError("upstream response exceeded configured size limit")
    return data


def resolve_latest_revision() -> str:
    url = f"https://api.github.com/repos/{DATA_REPOSITORY}/commits/master"
    try:
        payload = json.loads(_request(url, max_bytes=256 * 1024))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CatalogError("upstream commit metadata is not valid JSON") from exc
    return validate_revision(payload.get("sha", ""))


def download_archive(revision: str) -> bytes:
    revision = validate_revision(revision)
    url = f"https://codeload.github.com/{DATA_REPOSITORY}/tar.gz/{revision}"
    return _request(url, max_bytes=MAX_ARCHIVE_BYTES, timeout=60)


def _text(value, field: str, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise CatalogError(f"{field} must be a string")
    normalized = value.strip()
    if required and not normalized:
        raise CatalogError(f"{field} is required")
    if len(normalized) > MAX_TEXT_LENGTH:
        raise CatalogError(f"{field} exceeds maximum length")
    return normalized or None


def _https_url(value, field: str) -> str | None:
    value = _text(value, field)
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise CatalogError(f"{field} must be an absolute HTTPS URL without user information")
    if any(ord(char) < 32 for char in value):
        raise CatalogError(f"{field} contains control characters")
    return value


def _string_list(value, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 64:
        raise CatalogError(f"{field} must be a list of at most 64 strings")
    result = []
    for item in value:
        normalized = _text(item, field, required=True)
        result.append(normalized)
    return result


def _normalize_record(filename: str, raw: object, revision: str) -> dict:
    if not isinstance(raw, dict):
        raise CatalogError(f"{filename} must contain a YAML mapping")
    name = _text(raw.get("name"), "name", required=True)
    slug = SLUG_PATTERN.sub("-", PurePosixPath(filename).stem.lower()).strip("-")
    if not slug or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise CatalogError(f"{filename} does not produce a stable slug")

    archived = raw.get("archived", False)
    if not isinstance(archived, bool):
        raise CatalogError(f"{filename}: archived must be a boolean")

    release = raw.get("current_release")
    if release is not None and not isinstance(release, dict):
        raise CatalogError(f"{filename}: current_release must be a mapping")
    release_tag = _text(release.get("tag"), "current_release.tag") if release else None

    return {
        "catalog_id": f"awesome-selfhosted:{slug}",
        "name": name,
        "description": _text(raw.get("description"), "description"),
        "website_url": _https_url(raw.get("website_url"), "website_url"),
        "source_code_url": _https_url(raw.get("source_code_url"), "source_code_url"),
        "licenses": _string_list(raw.get("licenses"), "licenses"),
        "platforms": _string_list(raw.get("platforms"), "platforms"),
        "tags": _string_list(raw.get("tags"), "tags"),
        "archived": archived,
        "updated_at": _text(raw.get("updated_at"), "updated_at"),
        "current_release_tag": release_tag,
        "source_file": filename,
        "source_revision": revision,
        "source_repository": DATA_REPOSITORY,
        "catalog_license": DATA_LICENSE,
        "attribution": ATTRIBUTION,
        "lifecycle_status": "discovered",
        "invocation_status": "not_authorized",
    }


def parse_catalog_archive(archive_bytes: bytes, revision: str) -> list[dict]:
    revision = validate_revision(revision)
    if not isinstance(archive_bytes, bytes) or len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise CatalogError("archive is invalid or exceeds configured size limit")

    records = []
    seen_ids = set()
    unpacked_bytes = 0
    member_count = 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz")
    except (tarfile.TarError, OSError) as exc:
        raise CatalogError("upstream archive is not a valid gzip tar") from exc

    with archive:
        for member in archive:
            member_count += 1
            if member_count > MAX_FILES:
                raise CatalogError("archive contains too many entries")
            path = PurePosixPath(member.name)
            if ".." in path.parts or path.is_absolute():
                raise CatalogError("archive contains an unsafe path")
            if len(path.parts) < 3 or path.parts[-2] != "software" or path.suffix.lower() not in {".yml", ".yaml"}:
                continue
            if not member.isfile():
                raise CatalogError(f"software catalog entry is not a regular file: {path.name}")
            if member.size > MAX_RECORD_BYTES:
                raise CatalogError(f"catalog entry is too large: {path.name}")
            unpacked_bytes += member.size
            if unpacked_bytes > MAX_UNPACKED_BYTES:
                raise CatalogError("unpacked catalog exceeds configured size limit")
            stream = archive.extractfile(member)
            if stream is None:
                raise CatalogError(f"cannot read catalog entry: {path.name}")
            try:
                raw_text = stream.read(MAX_RECORD_BYTES + 1).decode("utf-8")
                if len(raw_text.encode("utf-8")) > MAX_RECORD_BYTES:
                    raise CatalogError(f"catalog entry is too large: {path.name}")
                raw = yaml.safe_load(raw_text)
            except (UnicodeDecodeError, yaml.YAMLError) as exc:
                raise CatalogError(f"invalid YAML in {path.name}") from exc
            record = _normalize_record(path.name, raw, revision)
            if record["catalog_id"] in seen_ids:
                raise CatalogError(f"duplicate stable catalog ID: {record['catalog_id']}")
            seen_ids.add(record["catalog_id"])
            records.append(record)

    if not records:
        raise CatalogError("upstream archive contains no software catalog records")
    return sorted(records, key=lambda item: item["catalog_id"])


def serialize_catalog(records: list[dict], revision: str) -> str:
    revision = validate_revision(revision)
    metadata = {
        "_record_type": "catalog_snapshot",
        "catalog_id": "catalog.awesome_selfhosted",
        "source_repository": DATA_REPOSITORY,
        "source_revision": revision,
        "catalog_license": DATA_LICENSE,
        "license_url": DATA_LICENSE_URL,
        "attribution": ATTRIBUTION,
        "sync_mode": "read_only",
        "discovery_only": True,
        "record_count": len(records),
    }
    lines = [json.dumps(metadata, ensure_ascii=False, sort_keys=True)]
    lines.extend(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in records)
    return "\n".join(lines) + "\n"


def sync(output: Path, revision: str | None = None, *, check: bool = False) -> tuple[int, str]:
    resolved = validate_revision(revision) if revision else resolve_latest_revision()
    archive = download_archive(resolved)
    records = parse_catalog_archive(archive, resolved)
    serialized = serialize_catalog(records, resolved)
    if check:
        try:
            existing = output.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise CatalogError(f"snapshot does not exist: {output}")
        if existing != serialized:
            raise CatalogError(f"snapshot is out of date: {output}")
        return len(records), resolved

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    os.replace(temporary, output)
    return len(records), resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", help="full immutable upstream commit SHA; defaults to latest master commit")
    parser.add_argument("--output", type=Path, default=Path("registry/catalogs/awesome-selfhosted.jsonl"))
    parser.add_argument("--check", action="store_true", help="fail if the committed snapshot differs; never write")
    args = parser.parse_args(argv)
    try:
        count, revision = sync(args.output, args.revision, check=args.check)
    except CatalogError as exc:
        print(f"catalog sync failed: {exc}", file=sys.stderr)
        return 1
    print(f"catalog sync {'verified' if args.check else 'written'}: {count} records at {revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
