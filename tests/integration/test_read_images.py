"""Integration tests for ``omr_diad.main.read_images``."""

from PIL import Image

from omr_diad.main import read_images
from tests.conftest import PDFS, requires_poppler


def test_read_images_from_embedded_pdf_images():
    pages = read_images(PDFS / "test3.pdf", convert_image=False)

    assert len(pages) == 16
    assert all(isinstance(page, Image.Image) for page in pages)


@requires_poppler
def test_read_images_with_pdf2image():
    pages = read_images(PDFS / "calibracion.pdf", convert_image=True)

    assert len(pages) == 50
    assert all(isinstance(page, Image.Image) for page in pages)
