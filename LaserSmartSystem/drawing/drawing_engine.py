"""
Drawing Engine Module — v2.0
Manages per-slide drawing state with undo/redo, eraser, and smooth interpolation.
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
import math


@dataclass
class Stroke:
    """A single drawn stroke."""
    points: List[Tuple[int, int]]
    color: str = "#FF3333"
    width: int = 3
    tool: str = "pen"  # "pen" or "eraser"


@dataclass
class SlideDrawingState:
    """Drawing state for one slide."""
    strokes: List[Stroke] = field(default_factory=list)
    redo_stack: List[Stroke] = field(default_factory=list)


class DrawingEngine:
    """Manages drawing state across all slides with undo/redo and eraser."""

    ERASER_RADIUS = 20

    def __init__(self):
        self._states: Dict[int, SlideDrawingState] = {}
        self.current_color: str = "#FF3333"
        self.current_width: int = 3
        self.current_tool: str = "pen"  # "pen" or "eraser"
        self.drawing_enabled: bool = False
        self._current_stroke_points: List[Tuple[int, int]] = []
        self._prev_point: Optional[Tuple[int, int]] = None

    def _get_state(self, slide_idx: int) -> SlideDrawingState:
        if slide_idx not in self._states:
            self._states[slide_idx] = SlideDrawingState()
        return self._states[slide_idx]

    def get_strokes(self, slide_idx: int) -> List[Stroke]:
        return self._get_state(slide_idx).strokes

    # ── stroke recording ─────────────────────────────────────────────────
    def begin_stroke(self):
        self._current_stroke_points = []
        self._prev_point = None

    def add_point(self, slide_idx: int, x: int, y: int, max_jump: int = 300) -> bool:
        """Add point to current stroke. Returns True if point accepted."""
        pt = (x, y)
        if self._prev_point is not None:
            dist = math.hypot(x - self._prev_point[0], y - self._prev_point[1])
            if dist > max_jump:
                self.end_stroke(slide_idx)
                self.begin_stroke()
                self._current_stroke_points.append(pt)
                self._prev_point = pt
                return True

        # Interpolate between previous and current if gap > 5px
        if self._prev_point is not None:
            dist = math.hypot(x - self._prev_point[0], y - self._prev_point[1])
            if dist > 5:
                steps = max(int(dist / 3), 1)
                px, py = self._prev_point
                for i in range(1, steps + 1):
                    t = i / steps
                    ix = int(px + (x - px) * t)
                    iy = int(py + (y - py) * t)
                    self._current_stroke_points.append((ix, iy))
            else:
                self._current_stroke_points.append(pt)
        else:
            self._current_stroke_points.append(pt)

        self._prev_point = pt
        return True

    def end_stroke(self, slide_idx: int):
        if len(self._current_stroke_points) >= 2:
            state = self._get_state(slide_idx)
            stroke = Stroke(
                points=self._current_stroke_points[:],
                color=self.current_color,
                width=self.current_width,
                tool=self.current_tool,
            )
            state.strokes.append(stroke)
            state.redo_stack.clear()
        self._current_stroke_points = []
        self._prev_point = None

    def get_current_stroke(self) -> Optional[Stroke]:
        if len(self._current_stroke_points) >= 2:
            return Stroke(
                points=self._current_stroke_points[:],
                color=self.current_color,
                width=self.current_width,
                tool=self.current_tool,
            )
        return None

    # ── eraser ───────────────────────────────────────────────────────────
    def erase_at(self, slide_idx: int, x: int, y: int, radius: int = 0):
        """Remove strokes that pass near (x, y)."""
        if radius <= 0:
            radius = self.ERASER_RADIUS
        state = self._get_state(slide_idx)
        remaining = []
        for stroke in state.strokes:
            if stroke.tool == "eraser":
                remaining.append(stroke)
                continue
            hit = False
            for px, py in stroke.points:
                if math.hypot(px - x, py - y) < radius:
                    hit = True
                    break
            if not hit:
                remaining.append(stroke)
        if len(remaining) != len(state.strokes):
            state.strokes = remaining

    # ── undo / redo ──────────────────────────────────────────────────────
    def undo(self, slide_idx: int) -> bool:
        state = self._get_state(slide_idx)
        if state.strokes:
            stroke = state.strokes.pop()
            state.redo_stack.append(stroke)
            return True
        return False

    def redo(self, slide_idx: int) -> bool:
        state = self._get_state(slide_idx)
        if state.redo_stack:
            stroke = state.redo_stack.pop()
            state.strokes.append(stroke)
            return True
        return False

    # ── clear ────────────────────────────────────────────────────────────
    def clear(self, slide_idx: int):
        state = self._get_state(slide_idx)
        state.strokes.clear()
        state.redo_stack.clear()
        self._current_stroke_points.clear()
        self._prev_point = None

    # ── toggle ───────────────────────────────────────────────────────────
    def toggle_drawing(self, slide_idx: int):
        self.drawing_enabled = not self.drawing_enabled
        if not self.drawing_enabled:
            self.end_stroke(slide_idx)
            self._prev_point = None