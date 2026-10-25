"""Backends de archivos para Vercel (disco efímero) y S3 compatible."""
from __future__ import annotations

import json
import mimetypes
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


BLOB_API = "https://blob.vercel-storage.com"


def _blob_token():
    return (
        getattr(settings, "BLOB_READ_WRITE_TOKEN", "")
        or getattr(settings, "VERCEL_BLOB_READ_WRITE_TOKEN", "")
        or ""
    ).strip()


@deconstructible
class VercelBlobStorage(Storage):
    """Sube a Vercel Blob con BLOB_READ_WRITE_TOKEN. El FileField guarda la URL."""

    def _headers(self, content_type="application/octet-stream"):
        token = _blob_token()
        if not token:
            raise RuntimeError(
                "Falta BLOB_READ_WRITE_TOKEN. En DEBUG el fallback es disco local."
            )
        return {
            "Authorization": f"Bearer {token}",
            "x-api-version": "7",
            "x-content-type": content_type,
            "x-add-random-suffix": "1",
            "access": "public",
        }

    def _open(self, name, mode="rb"):
        if not name.startswith("http"):
            raise FileNotFoundError(name)
        with urlopen(name) as response:
            return ContentFile(response.read(), name=name)

    def _save(self, name, content):
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        body = content.read() if hasattr(content, "read") else content
        request = Request(
            f"{BLOB_API}/{name.lstrip('/')}",
            data=body,
            headers=self._headers(content_type),
            method="PUT",
        )
        try:
            with urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detalle = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Vercel Blob rechazó el archivo ({exc.code}): {detalle}") from exc
        except URLError as exc:
            raise RuntimeError(f"No se pudo hablar con Vercel Blob: {exc}") from exc
        return payload.get("url") or name

    def exists(self, name):
        return False

    def url(self, name):
        return name

    def delete(self, name):
        if not name:
            return
        token = _blob_token()
        if not token:
            return
        request = Request(
            f"{BLOB_API}/delete",
            data=json.dumps({"urls": [name]}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "x-api-version": "7",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            urlopen(request)
        except (HTTPError, URLError):
            return

    def size(self, name):
        return 0
