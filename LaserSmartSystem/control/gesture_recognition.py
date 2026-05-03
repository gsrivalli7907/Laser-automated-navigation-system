import time

class ToggleClickDetector:
    def __init__(self, min_off_time=0.2, max_off_time=0.8, min_on_time=0.1):
        """
        Detects an ON -> OFF -> ON click sequence.
        min_off_time: Minimum duration (seconds) the laser must be OFF to be considered an intentional click toggle.
        max_off_time: Maximum duration (seconds) the laser can be OFF before the sequence resets.
        min_on_time: Minimum duration (seconds) the laser must have been ON prior to going OFF (prevents noise triggering).
        """
        self.min_off_time = min_off_time
        self.max_off_time = max_off_time
        self.min_on_time = min_on_time
        
        self.last_seen_time = 0
        self.last_off_time = 0
        self.was_on = False
        self.continuous_on_start = 0

    def update(self, is_visible):
        """
        Called every frame with whether the laser is currently visible.
        Returns True if a click sequence was completed this frame.
        """
        current_time = time.time()
        click_triggered = False

        if is_visible:
            # Transition OFF -> ON
            if not self.was_on:
                off_duration = current_time - self.last_off_time
                if self.min_off_time <= off_duration <= self.max_off_time:
                    # Valid ON -> OFF -> ON transition detected
                    click_triggered = True
                
                # Reset continuous ON tracker
                self.continuous_on_start = current_time

            self.last_seen_time = current_time
            self.was_on = True
        else:
            # Transition ON -> OFF
            if self.was_on:
                on_duration = current_time - self.continuous_on_start
                # Only record this OFF transition if the previous ON state was stable (not flutter noise)
                if on_duration >= self.min_on_time:
                    self.last_off_time = current_time
                else:
                    # If it was just noise, invalidate the tracking by setting last_off_time far back
                    self.last_off_time = 0
                    
            self.was_on = False

        return click_triggered