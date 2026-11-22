"""Private resume storage backends with stable, backend-tagged references."""
import os
import re
import uuid
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx


BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_RESUME_DIR = Path(os.getenv(
    "HIRESENSE_RESUME_STORAGE",
    str(BASE_DIR / "storage" / "resumes"),
))
DEFAULT_SUPABASE_BUCKET = "hiresense-resumes"
_SAFE_OBJECT_KEY = re.compile(r"^[A-Za-z0-9_-]{1,128}\.(?:pdf|docx)$", re.IGNORECASE)


class ResumeStorageError(Exception):
    """A storage operation failed without exposing credentials or paths."""


class ResumeObjectNotFound(ResumeStorageError):
    """A referenced resume object does not exist."""


def validate_storage_key(key: str) -> str:
    key = str(key)
    if (
        not _SAFE_OBJECT_KEY.fullmatch(key)
        or "/" in key
        or "\\" in key
        or key in {".", ".."}
    ):
        raise ResumeStorageError("The stored resume reference is invalid.")
    return key


class LocalResumeStorage:
    name = "local"

    def __init__(self, root: Path = LOCAL_RESUME_DIR):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        safe_key = validate_storage_key(key)
        path = (self.root / safe_key).resolve(strict=False)
        if not path.is_relative_to(self.root):
            raise ResumeStorageError("The stored resume reference is invalid.")
        return path

    def upload(self, key: str, contents: bytes, content_type: str, *, upsert: bool = False) -> None:
        del content_type  # Filesystem storage does not need MIME metadata.
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not upsert:
                raise ResumeStorageError("The generated resume key already exists.")
            temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            try:
                temporary_path.write_bytes(contents)
                os.replace(temporary_path, path)
            finally:
                temporary_path.unlink(missing_ok=True)
        except ResumeStorageError:
            raise
        except OSError as exc:
            raise ResumeStorageError("The local resume could not be stored.") from exc

    def retrieve(self, key: str) -> bytes:
        path = self._path(key)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise ResumeObjectNotFound("Resume file not found.") from exc
        except OSError as exc:
            raise ResumeStorageError("The local resume could not be read.") from exc

    def delete(self, key: str) -> None:
        path = self._path(key)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise ResumeStorageError("The local resume could not be deleted.") from exc

    def exists(self, key: str) -> bool:
        path = self._path(key)
        try:
            return path.is_file()
        except OSError as exc:
            raise ResumeStorageError("The local resume could not be checked.") from exc

    def key_from_legacy_path(self, reference: str) -> str:
        raw_path = str(reference)
        candidate = Path(raw_path)
        if candidate.is_absolute() and candidate.resolve(strict=False).is_relative_to(self.root):
            key = candidate.resolve(strict=False).name
        else:
            parts = [part for part in raw_path.replace("\\", "/").split("/") if part]
            normalized = [part.casefold() for part in parts]
            if len(parts) < 3 or normalized[-3:-1] != ["storage", "resumes"]:
                raise ResumeStorageError("The legacy resume reference is outside managed storage.")
            key = parts[-1]
        return validate_storage_key(key)


class SupabaseResumeStorage:
    name = "supabase"

    def __init__(self):
        self.base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        self.secret_key = os.getenv("SUPABASE_SECRET_KEY", "").strip()
        self.bucket = os.getenv(
            "SUPABASE_STORAGE_BUCKET", DEFAULT_SUPABASE_BUCKET
        ).strip()

        parsed_url = urlsplit(self.base_url)
        local_http_allowed = parsed_url.hostname in {"localhost", "127.0.0.1", "::1"}
        if not self.base_url or not self.secret_key or not self.bucket:
            raise ResumeStorageError(
                "Supabase resume storage requires SUPABASE_URL, "
                "SUPABASE_SECRET_KEY, and SUPABASE_STORAGE_BUCKET."
            )
        if parsed_url.scheme != "https" and not (parsed_url.scheme == "http" and local_http_allowed):
            raise ResumeStorageError("SUPABASE_URL must use HTTPS.")
        if not parsed_url.netloc or parsed_url.username or parsed_url.password:
            raise ResumeStorageError("SUPABASE_URL is invalid.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", self.bucket):
            raise ResumeStorageError("SUPABASE_STORAGE_BUCKET is invalid.")

        self.storage_url = f"{self.base_url}/storage/v1"
        # Current Supabase secret API keys belong in `apikey` only; they are
        # not JWTs and must not be sent as Authorization: Bearer credentials.
        self.headers = {"apikey": self.secret_key}

    def _object_url(self, key: str, *, include_key: bool = True) -> str:
        safe_key = validate_storage_key(key)
        bucket = quote(self.bucket, safe="")
        url = f"{self.storage_url}/object/{bucket}"
        return f"{url}/{quote(safe_key, safe='')}" if include_key else url

    @staticmethod
    def _raise_for_response(response: httpx.Response, *, missing_is_ok: bool = False) -> bool:
        if missing_is_ok and response.status_code == 404:
            return False
        if response.status_code == 404:
            raise ResumeObjectNotFound("Resume file not found.")
        if not response.is_success:
            raise ResumeStorageError(
                f"Supabase Storage request failed (HTTP {response.status_code})."
            )
        return True

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        request_headers = {**self.headers, **kwargs.pop("headers", {})}
        try:
            with httpx.Client(timeout=30.0, follow_redirects=False) as client:
                return client.request(method, url, headers=request_headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ResumeStorageError("Supabase Storage is unavailable.") from exc

    def upload(self, key: str, contents: bytes, content_type: str, *, upsert: bool = False) -> None:
        response = self._request(
            "POST",
            self._object_url(key),
            content=contents,
            headers={"Content-Type": content_type, "x-upsert": str(upsert).lower()},
        )
        self._raise_for_response(response)

    def retrieve(self, key: str) -> bytes:
        response = self._request("GET", self._object_url(key))
        self._raise_for_response(response)
        return response.content

    def delete(self, key: str) -> None:
        response = self._request(
            "POST",
            self._object_url(key, include_key=False),
            json={"prefixes": [validate_storage_key(key)]},
        )
        self._raise_for_response(response, missing_is_ok=True)

    def exists(self, key: str) -> bool:
        safe_key = validate_storage_key(key)
        bucket = quote(self.bucket, safe="")
        list_url = f"{self.storage_url}/object/list/{bucket}"
        page_size = 100
        offset = 0

        while True:
            response = self._request(
                "POST",
                list_url,
                json={
                    # Resume keys are stored at the bucket root. `search` narrows
                    # the listing; exact name comparison below avoids treating
                    # another object with the same prefix as a match.
                    "prefix": "",
                    "search": safe_key,
                    "limit": page_size,
                    "offset": offset,
                },
            )

            # A 404 from the list endpoint indicates an API/bucket problem, not
            # a missing object. A missing object is an empty successful list.
            if not response.is_success:
                raise ResumeStorageError(
                    f"Supabase Storage list request failed (HTTP {response.status_code})."
                )

            try:
                objects = response.json()
            except ValueError as exc:
                raise ResumeStorageError(
                    "Supabase Storage returned an invalid object list."
                ) from exc

            if not isinstance(objects, list):
                raise ResumeStorageError(
                    "Supabase Storage returned an invalid object list."
                )

            if any(
                isinstance(item, dict) and item.get("name") == safe_key
                for item in objects
            ):
                return True
            if len(objects) < page_size:
                return False
            offset += page_size


def get_storage_backend(name: str | None = None):
    backend = (name or os.getenv("RESUME_STORAGE_BACKEND", "local")).strip().lower()
    if backend == "local":
        return LocalResumeStorage()
    if backend == "supabase":
        return SupabaseResumeStorage()
    raise ResumeStorageError("RESUME_STORAGE_BACKEND must be 'local' or 'supabase'.")


def reference_for(backend: str, key: str) -> str:
    if backend not in {"local", "supabase"}:
        raise ResumeStorageError("The resume storage backend is invalid.")
    return f"{backend}:{validate_storage_key(key)}"


def storage_for_reference(reference: str):
    raw_reference = str(reference)
    if ":" in raw_reference:
        backend_name, key = raw_reference.split(":", 1)
        if backend_name in {"local", "supabase"}:
            key = validate_storage_key(key)
            return get_storage_backend(backend_name), key, reference_for(backend_name, key)

    local_storage = LocalResumeStorage()
    key = local_storage.key_from_legacy_path(raw_reference)
    return local_storage, key, reference_for("local", key)


def configured_storage_reference(key: str) -> tuple[object, str, str]:
    storage = get_storage_backend()
    safe_key = validate_storage_key(key)
    return storage, safe_key, reference_for(storage.name, safe_key)
