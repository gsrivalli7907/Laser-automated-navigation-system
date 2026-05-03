"""
Voice Control Module
Runs speech recognition in a background thread and fires callbacks.
Also monitors audio energy to detect overlapping / multiple voices.
"""

import threading
import speech_recognition as sr
from typing import Callable, Optional

# Energy thresholds
MULTI_VOICE_ENERGY_THRESHOLD = 3000  # RMS energy suggesting multiple voices


class VoiceController:
    """Continuous voice-command listener running in a daemon thread."""

    COMMANDS = {
        "next": "next",
        "previous": "previous",
        "back": "previous",
        "clear": "clear",
        "start drawing": "start_drawing",
        "stop drawing": "stop_drawing",
    }

    def __init__(
        self,
        on_command: Optional[Callable[[str], None]] = None,
        on_multi_voice: Optional[Callable[[bool], None]] = None,
    ):
        self.on_command = on_command
        self.on_multi_voice = on_multi_voice
        self.recognizer = sr.Recognizer()
        self.microphone: Optional[sr.Microphone] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.listening = False

    def start(self) -> bool:
        """Start listening in a background thread. Returns False on mic error."""
        try:
            self.microphone = sr.Microphone()
            # Calibrate for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except (OSError, AttributeError) as e:
            print(f"[VoiceController] Microphone error: {e}")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False

    # ── internal ─────────────────────────────────────────────────────────
    def _listen_loop(self):
        while self._running:
            try:
                with self.microphone as source:
                    self.listening = True
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    self.listening = False

                # Check energy level for multiple-voice heuristic
                raw = audio.get_raw_data()
                import numpy as np
                samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
                rms = float(np.sqrt(np.mean(samples ** 2)))
                if self.on_multi_voice:
                    self.on_multi_voice(rms > MULTI_VOICE_ENERGY_THRESHOLD)

                # Recognise speech (Google Web API — needs internet)
                try:
                    text = self.recognizer.recognize_google(audio).lower().strip()
                    print(f"[Voice] Heard: {text}")
                    for phrase, cmd in self.COMMANDS.items():
                        if phrase in text:
                            if self.on_command:
                                self.on_command(cmd)
                            break
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[Voice] API error: {e}")

            except sr.WaitTimeoutError:
                self.listening = False
            except Exception as e:
                print(f"[Voice] Error: {e}")
                self.listening = False