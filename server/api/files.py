"""File sanitization endpoint."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from server.auth import get_current_api_key
from server.db.models import ApiKey
from server.helpers import get_wonderwall_for_key
from server.rate_limiter import check_rate_limit
from server.schemas.responses import FileSanitizeResponse

router = APIRouter(prefix="/v1/file", tags=["File"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/sanitize")
async def sanitize_file(
    file: UploadFile,
    api_key: ApiKey = Depends(get_current_api_key),
):
    """Validate file by magic bytes and strip EXIF metadata.

    Returns the cleaned file bytes on success, or a JSON error on rejection.
    """
    check_rate_limit(api_key.id, api_key.rate_limit)

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 10MB)")

    instance = await get_wonderwall_for_key(api_key)
    ok, cleaned, message = instance.sanitize_file(data, file.content_type or "")

    if ok:
        return Response(
            content=cleaned,
            media_type=file.content_type or "application/octet-stream",
            headers={
                "X-Wonderwall-Status": "sanitized",
                "X-Wonderwall-Message": message,
            },
        )
    else:
        return FileSanitizeResponse(ok=False, message=message, cleaned_size_bytes=0)
