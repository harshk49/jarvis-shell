import sys
import os
from contextlib import contextmanager

@contextmanager
def suppress_stderr():
    """Context manager to suppress C-level standard error (useful for PyAudio ALSA spam)."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)


def get_recognizer():
    try:
        import speech_recognition as sr
        return sr
    except ImportError:
        return None


def record_to_text(timeout: int = 5) -> str | None:
    """
    Listen to the system microphone and convert speech to string natively using Google's free inference.
    Requires SpeechRecognition and PyAudio to be locally installed.
    """
    sr = get_recognizer()
    if not sr:
        print("\r\033[K\033[91m✗ Missing SpeechRecognition or PyAudio modules. Run 'pip install -r requirements.txt'\033[0m")
        return None

    r = sr.Recognizer()
    
    # Optional print statement mapping handled by main UI wrapper
    try:
        with suppress_stderr():
            mic = sr.Microphone()
            
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=15)
            
        return r.recognize_google(audio)
    
    except sr.WaitTimeoutError:
        # User pressed key but said nothing inside timeframe
        return None
    except sr.UnknownValueError:
        # Audio registered but unreadable (noise)
        return None
    except sr.RequestError as e:
        print(f"\r\033[K\033[91m✗ Google Speech API unreachable: {e}\033[0m")
        return None
    except Exception as e:
        print(f"\r\033[K\033[91m✗ Microphone Error (PortAudio may be missing): {e}\033[0m")
        return None
