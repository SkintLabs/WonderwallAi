"""Tests for the File Sanitizer layer."""

import io
import pytest
from wonderwallai.layers.file_sanitizer import FileSanitizer, PILLOW_AVAILABLE


class TestMimeValidation:
    def test_valid_jpeg_magic_bytes(self):
        fs = FileSanitizer()
        # JPEG magic bytes: FF D8 FF
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        is_valid, detected = fs.validate_mime(jpeg_data)
        assert is_valid
        assert "jpeg" in detected.lower() or detected == "image/jpeg"

    def test_valid_png_magic_bytes(self):
        fs = FileSanitizer()
        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        is_valid, detected = fs.validate_mime(png_data)
        assert is_valid
        assert "png" in detected.lower() or detected == "image/png"

    def test_blocked_mime_type(self):
        fs = FileSanitizer(allowed_mimes={"image/jpeg"})
        # PNG data but only JPEG allowed
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        is_valid, detected = fs.validate_mime(png_data)
        assert not is_valid
        assert "blocked" in detected

    def test_unknown_file_type(self):
        fs = FileSanitizer()
        is_valid, detected = fs.validate_mime(b'\x00\x01\x02\x03')
        assert not is_valid

    def test_custom_allowed_mimes(self):
        fs = FileSanitizer(allowed_mimes={"application/pdf", "image/jpeg"})
        assert "application/pdf" in fs.allowed_mimes
        assert "image/jpeg" in fs.allowed_mimes


class TestExifStripping:
    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
    def test_strip_exif_produces_valid_image(self):
        from PIL import Image

        # Create a test image
        img = Image.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        original_data = buf.getvalue()

        fs = FileSanitizer()
        stripped = fs.strip_exif(original_data)
        assert len(stripped) > 0

        # Verify it's still a valid image
        result_img = Image.open(io.BytesIO(stripped))
        assert result_img.size == (10, 10)


class TestFullPipeline:
    @pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow not installed")
    def test_sanitize_jpeg(self):
        from PIL import Image

        img = Image.new("RGB", (10, 10), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        fs = FileSanitizer()
        ok, cleaned, msg = fs.sanitize(buf.getvalue())
        assert ok
        assert len(cleaned) > 0
        assert "Sanitized" in msg
