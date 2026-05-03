"""
PDF Handler Module
Converts PDF pages to PIL Images for display.
"""

import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Optional


class PDFHandler:
    """Handles PDF loading and page-to-image conversion."""

    def __init__(self):
        self.doc: Optional[fitz.Document] = None
        self.page_images: List[Image.Image] = []
        self.current_page: int = 0

    def load(self, path: str, dpi: int = 200) -> bool:
        """Load a PDF and render all pages as PIL Images.
        
        Args:
            path: Path to the PDF file.
            dpi: Resolution for rendering (higher = sharper but slower).
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        try:
            self.doc = fitz.open(path)
            self.page_images = []
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for page in self.doc:
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                self.page_images.append(img)
            self.current_page = 0
            return True
        except Exception as e:
            print(f"[PDFHandler] Error loading PDF: {e}")
            return False

    @property
    def total_pages(self) -> int:
        return len(self.page_images)

    def get_page(self, index: int) -> Optional[Image.Image]:
        """Return the PIL Image for the given page index."""
        if 0 <= index < self.total_pages:
            return self.page_images[index]
        return None

    def next_page(self) -> Optional[Image.Image]:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        return self.get_page(self.current_page)

    def prev_page(self) -> Optional[Image.Image]:
        if self.current_page > 0:
            self.current_page -= 1
        return self.get_page(self.current_page)