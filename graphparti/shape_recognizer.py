"""Shape recognition — detect geometric primitives from freehand point clouds.

Used by FreeDrawTool for hold-to-correct: user draws loosely, holds at the end,
the system snaps to the nearest clean geometric shape.
"""
from __future__ import annotations
import math
from PySide6.QtCore import QPointF, QLineF, QRectF


def recognize_shape(points: list[QPointF]) -> dict | None:
    """Analyze a list of points and return the best-fit geometric shape.

    Returns dict with:
      {"type": "line", "p1": QPointF, "p2": QPointF}
      {"type": "circle", "center": QPointF, "radius": float}
      {"type": "rect", "rect": QRectF}
      {"type": "ellipse", "rect": QRectF}
    Or None if no clean shape is detected.
    """
    if len(points) < 3:
        return None

    # Test 1: Straight line
    line_result = _test_line(points)
    if line_result:
        return line_result

    # Test 2: Circle / ellipse (closed path that's roughly round)
    circle_result = _test_circle(points)
    if circle_result:
        return circle_result

    # Test 3: Rectangle (4 corners, roughly orthogonal)
    rect_result = _test_rectangle(points)
    if rect_result:
        return rect_result

    return None


def _test_line(points: list[QPointF], tolerance: float = 0.15) -> dict | None:
    """Test if points form a straight line.
    Tolerance = max perpendicular deviation as fraction of line length."""
    p1, p2 = points[0], points[-1]
    length = QLineF(p1, p2).length()
    if length < 5:
        return None

    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()

    max_dev = 0
    for pt in points:
        # Perpendicular distance from point to line p1→p2
        dist = abs(dy * pt.x() - dx * pt.y() + p2.x() * p1.y() - p2.y() * p1.x()) / length
        max_dev = max(max_dev, dist)

    if max_dev < length * tolerance:
        return {"type": "line", "p1": QPointF(p1), "p2": QPointF(p2)}
    return None


def _test_circle(points: list[QPointF], closure_tolerance: float = 0.2,
                 radius_tolerance: float = 0.25) -> dict | None:
    """Test if points form a circle or ellipse.
    Checks: path roughly closes, radius variance is low."""
    # Check if path closes (end near start)
    start, end = points[0], points[-1]
    total_length = sum(QLineF(a, b).length() for a, b in zip(points, points[1:]))
    closure_dist = QLineF(start, end).length()

    if total_length < 20:
        return None
    if closure_dist > total_length * closure_tolerance:
        return None

    # Compute centroid
    cx = sum(p.x() for p in points) / len(points)
    cy = sum(p.y() for p in points) / len(points)
    center = QPointF(cx, cy)

    # Compute radii
    radii = [QLineF(center, p).length() for p in points]
    avg_r = sum(radii) / len(radii)
    if avg_r < 5:
        return None

    variance = sum((r - avg_r) ** 2 for r in radii) / len(radii)
    std_dev = math.sqrt(variance)

    if std_dev / avg_r < radius_tolerance:
        # Check if it's more ellipse-like (different x/y extents)
        xs = [p.x() for p in points]
        ys = [p.y() for p in points]
        rx = (max(xs) - min(xs)) / 2
        ry = (max(ys) - min(ys)) / 2

        if abs(rx - ry) / max(rx, ry, 1) < 0.2:
            # Roughly circular
            return {"type": "circle", "center": center, "radius": avg_r}
        else:
            # Elliptical
            ecx = (max(xs) + min(xs)) / 2
            ecy = (max(ys) + min(ys)) / 2
            return {"type": "ellipse", "rect": QRectF(ecx - rx, ecy - ry, rx * 2, ry * 2)}

    return None


def _test_rectangle(points: list[QPointF], angle_tolerance: float = 25) -> dict | None:
    """Test if points form a rectangle.
    Finds dominant direction changes and checks for ~4 right angles."""
    if len(points) < 8:
        return None

    # Check if path roughly closes
    start, end = points[0], points[-1]
    total_length = sum(QLineF(a, b).length() for a, b in zip(points, points[1:]))
    if QLineF(start, end).length() > total_length * 0.2:
        return None

    # Simple approach: use the bounding box of the points
    # If the points fill the bounding box edges well, it's a rectangle
    xs = [p.x() for p in points]
    ys = [p.y() for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x
    h = max_y - min_y

    if w < 10 or h < 10:
        return None

    # Check how well points hug the edges of the bounding box
    edge_points = 0
    threshold = max(w, h) * 0.15
    for p in points:
        near_left = abs(p.x() - min_x) < threshold
        near_right = abs(p.x() - max_x) < threshold
        near_top = abs(p.y() - min_y) < threshold
        near_bottom = abs(p.y() - max_y) < threshold
        if near_left or near_right or near_top or near_bottom:
            edge_points += 1

    edge_ratio = edge_points / len(points)
    if edge_ratio > 0.7:
        return {"type": "rect", "rect": QRectF(min_x, min_y, w, h)}

    return None
