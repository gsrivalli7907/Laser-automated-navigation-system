import cv2

from laser_detection.laser_detector import LaserDetector
from drawing.drawing_engine import DrawingEngine
from export.export_handler import ExportHandler
from export.pdf_handler import PDFHandler
from control.voice_control import VoiceController
from control.gesture_recognition import GestureController
from control.mouse_control import MouseController


class LaserSystem:
    def __init__(self):
        self.detector = LaserDetector()
        self.drawer = DrawingEngine()
        self.exporter = ExportHandler()
        self.pdf = PDFHandler()
        self.voice = VoiceController()
        self.gesture = GestureController()
        self.mouse = MouseController()

        self.mode = "draw"
        self.running = True

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

            # Laser detection
            frame = self.detector.get_frame()
            x, y = self.detector.detect(frame)

            if x is None:
                continue

            # Mode-based execution
            if self.mode == "draw":
                self.drawer.draw(x, y)

            elif self.mode == "mouse":
                self.mouse.move(x, y)

            elif self.mode == "navigate":
                self.navigate(x, y)

            self.drawer.show()

            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                self.exporter.save(self.drawer.canvas)

            elif key == ord('p'):
                self.pdf.save(self.drawer.canvas)

            elif key == ord('q'):
                break

        cv2.destroyAllWindows()

    def handle_voice(self, cmd):
        if cmd == "draw":
            self.mode = "draw"
        elif cmd == "mouse":
            self.mode = "mouse"
        elif cmd == "navigate":
            self.mode = "navigate"
        elif cmd == "save":
            self.exporter.save(self.drawer.canvas)
        elif cmd == "pdf":
            self.pdf.save(self.drawer.canvas)
        elif cmd == "clear":
            self.drawer.clear()
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
            self.drawer.clear()

    def navigate(self, x, y):
        print(f"Navigating to ({x}, {y})")


if __name__ == "__main__":
    LaserSystem().run()