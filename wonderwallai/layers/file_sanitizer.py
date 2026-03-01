"""
WonderwallAi — File Sanitizer Layer
Validates uploads by magic bytes (not extension) and strips EXIF metadata.
"""

import io
import logging
from typing import Optional, Set, Tuple

logger = logging.getLogger("wonderwallai.file_sanitizer")

try:
    import filetype
    FILETYPE_AVAILABLE = True
except ImportError:
    FILETYPE_AVAILABLE = False
    logger.info(
        "filetype package not installed — file validation disabled. "
        "Install with: pip install wonderwallai[files]"
    )

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.info(
        "Pillow package not installed — EXIF stripping disabled. "
        "Install with: pip install wonderwallai[files]"
    )


class FileSanitizer:
    """
    Validates uploaded files by magic bytes and strips EXIF metadata.

    Args:
        allowed_mimes: Set of allowed MIME types. Defaults to JPEG and PNG.
    """

    def __init__(self, allowed_mimes: Optional[Set[str]] = None):
        self.allowed_mimes = allowed_mimes or {"image/jpeg", "image/png"}

    def validate_mime(self, data: bytes) -> Tuple[bool, str]:
        """Check magic bytes. Returns (is_valid, detected_mime_or_error)."""
        if not FILETYPE_AVAILABLE:
            return (True, "filetype_unavailable")

        kind = filetype.guess(data)
        if kind is None:
            return (False, "unknown_file_type")

        if kind.mime not in self.allowed_mimes:
            logger.warning(f"Blocked file type: {kind.mime}")
            return (False, f"blocked_mime:{kind.mime}")

        return (True, kind.mime)

    def strip_exif(self, image_data: bytes) -> bytes:
        """Strip all EXIF/metadata from an image by re-creating pixel data."""
        if not PILLOW_AVAILABLE:
            return image_data

        try:
            image_stream = io.BytesIO(image_data)
            original = Image.open(image_stream)

            # Create new image with only pixel data (strips EXIF, comments, etc.)
            clean = Image.new(original.mode, original.size)
            clean.putdata(list(original.getdata()))

            clean_stream = io.BytesIO()
            fmt = original.format or "PNG"
            clean.save(clean_stream, format=fmt)
            return clean_stream.getvalue()

        except Exception as e:
            logger.error(f"EXIF stripping failed: {e}")
            return image_data

    def sanitize(
        self, data: bytes, claimed_mime: str = ""
    ) -> Tuple[bool, bytes, str]:
        """
        Full pipeline: validate magic bytes + strip metadata.

        Returns:
            Tuple of (ok, cleaned_data, message).
        """
        is_valid, detected = self.validate_mime(data)
        if not is_valid:
            return (False, b"", f"File rejected: {detected}")

        if detected in ("image/jpeg", "image/png"):
            cleaned = self.strip_exif(data)
            return (True, cleaned, f"Sanitized {detected}")

        return (True, data, f"Passed: {detected}")
