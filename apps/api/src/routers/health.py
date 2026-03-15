import importlib.metadata

from fastapi import APIRouter

router = APIRouter()

try:
    _VERSION = importlib.metadata.version("ed-insights-api")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "unknown"


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": _VERSION}
