"""
Export Handler — saves annotated slides as images or a PDF.
"""

import os
from typing import List, Tuple
from PIL import Image, ImageDraw
from drawing.drawing_engine import Stroke


class ExportHandler:
    """Export annotated slides."""

    @staticmethod
    def render_strokes_on_image(
        base_img: Image.Image,
        strokes: List[Stroke],
        screen_w: int, screen_h: int,
    ) -> Image.Image:
        """Render drawing strokes onto a copy of the base image."""
        img = base_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        img_w, img_h = img.size
        sx = img_w / screen_w
        sy = img_h / screen_h

        for stroke in strokes:
            if stroke.tool == "eraser" or len(stroke.points) < 2:
                continue
            color = stroke.color
            scaled_pts = [(int(x * sx), int(y * sy)) for x, y in stroke.points]
            for i in range(len(scaled_pts) - 1):
                draw.line([scaled_pts[i], scaled_pts[i+1]], fill=color, width=max(1, int(stroke.width * sx)))

        return Image.alpha_composite(img, overlay).convert("RGB")

    @staticmethod
    def export_slides(
        page_images: list,
        drawing_states: dict,
        screen_w: int, screen_h: int,
        output_dir: str,
        fmt: str = "png",
    ) -> List[str]:
        """Export all slides with annotations to output_dir. Returns list of file paths."""
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for i, img in enumerate(page_images):
            strokes = drawing_states.get(i, [])
            annotated = ExportHandler.render_strokes_on_image(img, strokes, screen_w, screen_h)
            path = os.path.join(output_dir, f"slide_{i+1:03d}.{fmt}")
            annotated.save(path)
            paths.append(path)
        return paths

    @staticmethod
    def export_pdf(
        page_images: list,
        drawing_states: dict,
        screen_w: int, screen_h: int,
        output_path: str,
    ) -> str:
        """Export all annotated slides as a single PDF."""
        images = []
        for i, img in enumerate(page_images):
            strokes = drawing_states.get(i, [])
            annotated = ExportHandler.render_strokes_on_image(img, strokes, screen_w, screen_h)
            images.append(annotated)

        if images:
            images[0].save(output_path, save_all=True, append_images=images[1:])
        return output_path