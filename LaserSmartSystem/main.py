import cv2

from laser_detection.laser_detector import LaserDetector
from drawing.drawing_engine import DrawingEngine
from export.export_handler import ExportHandler
from export.pdf_handler import PDFHandler
from control.voice_control import VoiceController
from control.gesture_recognition import ToggleClickDetector
from control.mouse_control import MouseController


class LaserSystem:
    def __init__(self):
        self.detector = LaserDetector()
        self.detector.open_camera()

        self.drawer = DrawingEngine()
        self.exporter = ExportHandler()
        self.pdf = PDFHandler()
        self.voice = VoiceController()
        self.gesture = ToggleClickDetector()
        self.mouse = MouseController()

        self.mode = "draw"
        self.running = True

        self.canvas = None
        self.prev = None

    def run(self):
        while self.running:

            # Voice control
            try:
                cmd = self.voice.listen()
                if cmd:
                    self.handle_voice(cmd)
            except:
                pass

            # Gesture control
            try:
                gesture = self.gesture.detect()
                if gesture:
                    self.handle_gesture(gesture)
            except:
                pass

            frame = self.detector.read_frame()
            if frame is None:
                continue

            result = self.detector.detect(frame)
            if result is None:
                continue

            x, y = result

            if self.canvas is None:
                self.canvas = frame.copy()

            display = frame.copy()

            # ======================
            # MODES
            # ======================

            if self.mode == "draw":
                cv2.circle(display, (x, y), 3, (0, 0, 255), -1)
                cv2.circle(self.canvas, (x, y), 3, (0, 0, 255), -1)

            elif self.mode == "mouse":
                h, w, _ = frame.shape

                norm_x = x / w
                norm_y = y / h

                self.mouse.move_to_normalized(norm_x, norm_y)

                if self.prev:
                    dx = abs(self.prev[0] - x)
                    dy = abs(self.prev[1] - y)

                    if dx < 5 and dy < 5:
                        self.mouse.single_click()

                self.prev = (x, y)

            elif self.mode == "navigate":
                self.navigate(x, y)

            # SHOW
            cv2.imshow("Laser System", display)

            key = cv2.waitKey(1) & 0xFF

            # ======================
            # CONTROLS
            # ======================

            if key == ord('q'):
                break

            elif key == ord('s'):
                self.exporter.save(self.canvas)

            elif key == ord('p'):
                self.pdf.save(self.canvas)

            elif key == ord('c'):
                self.canvas = frame.copy()

            elif key == ord('d'):
                self.mode = "draw"

            elif key == ord('m'):
                self.mode = "mouse"

            elif key == ord('n'):
                self.mode = "navigate"

        self.detector.release_camera()
        cv2.destroyAllWindows()

    def handle_voice(self, cmd):
        if cmd == "draw":
            self.mode = "draw"
        elif cmd == "mouse":
            self.mode = "mouse"
        elif cmd == "navigate":
            self.mode = "navigate"
        elif cmd == "save":
            self.exporter.save(self.canvas)
        elif cmd == "pdf":
            self.pdf.save(self.canvas)
        elif cmd == "clear":
            self.canvas = None
        elif cmd == "stop":
            self.running = False

    def handle_gesture(self, g):
        if g == "fist":
            self.mode = "navigate"
        elif g == "open":
            self.mode = "draw"
        elif g == "three":
            self.mode = "mouse"
        elif g == "two":
            self.canvas = None

    def navigate(self, x, y):
        print(f"Navigating to ({x}, {y})")


if __name__ == "__main__":
    LaserSystem().run()
    