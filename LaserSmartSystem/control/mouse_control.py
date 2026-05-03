import pyautogui
import time

class MouseController:
    def __init__(self):
        # Configure PyAutoGUI for minimum latency
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.0

        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        self.last_click_time = 0
        self.cooldown_time = 0.3  # Seconds to wait before allowing another click

    def can_click(self):
        """Check if enough time has passed to perform another click."""
        current_time = time.time()
        if (current_time - self.last_click_time) > self.cooldown_time:
            self.last_click_time = current_time
            return True
        return False

    def move_to_normalized(self, norm_x, norm_y):
        """
        Move the mouse to a position given by normalized coordinates [0.0, 1.0].
        Calculates the real screen pixel dynamically.
        """
        # Constrain between 0.0 and 1.0
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        screen_x = int(norm_x * self.screen_width)
        screen_y = int(norm_y * self.screen_height)
        
        pyautogui.moveTo(screen_x, screen_y)

    def single_click(self):
        """Trigger a single left click."""
        if self.can_click():
            print("[MouseControl] Single Click executed.")
            pyautogui.click()