"""Drive folder authorisation and file-index surface (PRD 9).

The endpoints model the DRV-00x requirements. File monitoring and checksum
capture (DRV-003, DRV-004) are represented as recorded index entries; the live
Drive change-watch subscription is a later deliverable.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/drive", tags=["Google Drive Integration"])

# Minimum necessary OAuth scopes (DRV-001).
REQUIRED_SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

_authorised_folders: dict[str, dict] = {}
_file_index: list[dict] = []


class FolderAuthorisation(BaseModel):
    folder_id: str = Field(description="Google Drive folder id to authorise (DRV-002).")
    programme_id: str | None = None


@router.get("/scopes")
def required_scopes() -> list[str]:
    """The least-privilege scopes SAGE requests (DRV-001)."""

    return REQUIRED_SCOPES


@router.post("/folders", status_code=201)
def authorise_folder(payload: FolderAuthorisation) -> dict:
    """Explicitly authorise a folder for access (DRV-002)."""

    entry = {"folder_id": payload.folder_id, "programme_id": payload.programme_id}
    _authorised_folders[payload.folder_id] = entry
    return entry


@router.get("/folders")
def list_authorised_folders() -> list[dict]:
    return list(_authorised_folders.values())


class IndexedFile(BaseModel):
    file_id: str
    version: str
    checksum: str
    owner: str
    application_id: str | None = None


@router.post("/index", status_code=201)
def index_file(payload: IndexedFile) -> dict:
    """Record file id, version, checksum, owner and association (DRV-004)."""

    record = payload.model_dump()
    record["index_id"] = str(uuid4())
    _file_index.append(record)
    return record


@router.get("/index")
def list_indexed_files() -> list[dict]:
    return _file_index
