"""
Laser Detector Module — v2.0
Enhanced with Kalman filter, adaptive thresholding, and better noise reduction.
"""

import cv2
import numpy as np
from collections import deque
from typing import Optional, Tuple

# HSV ranges for common laser colours
LASER_PROFILES = {
    "green": [
        (np.array([35, 60, 180]), np.array([85, 255, 255])),
    ],
    "red": [
        (np.array([0, 60, 180]), np.array([12, 255, 255])),
        (np.array([168, 60, 180]), np.array([180, 255, 255])),
    ],
}

MIN_AREA = 8
MAX_AREA = 4000
SMOOTH_WINDOW = 7
KALMAN_PROCESS_NOISE = 1e-2
KALMAN_MEASUREMENT_NOISE = 1e-1


class LaserDetector:
    """Detects a laser point from a webcam frame with Kalman smoothing."""

    def __init__(self, camera_index: int = 0):
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_index = camera_index
        self._history: deque = deque(maxlen=SMOOTH_WINDOW)
        self._kalman = self._init_kalman()
        self._kalman_initialized = False
        self._lost_frames = 0
        self._max_lost = 4  # frames before clearing history

    def _init_kalman(self):
        kf = cv2.KalmanFilter(4, 2)
        kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]], np.float32)
        kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]], np.float32)
        kf.processNoiseCov = np.eye(4, dtype=np.float32) * KALMAN_PROCESS_NOISE
        kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * KALMAN_MEASUREMENT_NOISE
        return kf

    def open_camera(self) -> bool:
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("[LaserDetector] Camera not found.")
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        return True

    def release_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def read_frame(self) -> Optional[np.ndarray]:
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def detect(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """Return Kalman-smoothed (x, y) of detected laser point, or None."""
        if frame is None:
            return None, None
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Boost brightness for low-light
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, 30)
        hsv_bright = cv2.merge([h, s, v])

        combined_mask = np.zeros(frame.shape[:2], dtype=np.uint8)

        for color_ranges in LASER_PROFILES.values():
            for lower, upper in color_ranges:
                mask = cv2.inRange(hsv_bright, lower, upper)
                combined_mask = cv2.bitwise_or(combined_mask, mask)

        # Bright overexposed spots
        bright_mask = cv2.inRange(hsv, np.array([0, 0, 240]), np.array([180, 70, 255]))
        combined_mask = cv2.bitwise_or(combined_mask, bright_mask)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if MIN_AREA < area < MAX_AREA:
                # Check circularity
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity < 0.3:
                    continue
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                brightness = float(v[min(cy, v.shape[0]-1), min(cx, v.shape[1]-1)])
                score = brightness * circularity
                if score > best_score:
                    best_score = score
                    best = (cx, cy)

        if best is None:
            self._lost_frames += 1
            if self._lost_frames > self._max_lost:
                self._history.clear()
                self._kalman_initialized = False
            return None

        self._lost_frames = 0
        self._history.append(best)

        # Kalman filter
        measurement = np.array([[np.float32(best[0])], [np.float32(best[1])]])
        if not self._kalman_initialized:
            self._kalman.statePre = np.array([
                [np.float32(best[0])], [np.float32(best[1])],
                [0.], [0.]], np.float32)
            self._kalman.statePost = self._kalman.statePre.copy()
            self._kalman_initialized = True

        self._kalman.predict()
        corrected = self._kalman.correct(measurement)
        kx, ky = int(corrected[0][0]), int(corrected[1][0])

        # Blend Kalman with moving average
        avg_x = int(np.mean([p[0] for p in self._history]))
        avg_y = int(np.mean([p[1] for p in self._history]))
        fx = int(0.6 * kx + 0.4 * avg_x)
        fy = int(0.6 * ky + 0.4 * avg_y)

        return (fx, fy)