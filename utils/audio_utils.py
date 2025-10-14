# audio_utils.py
try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
    PYDUB_AVAILABLE = True
except Exception:
    PYDUB_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except Exception:
    PLAYSOUND_AVAILABLE = False

def play_audio_file(path):
    """Play an audio file if a backend is available."""
    if PYDUB_AVAILABLE:
        seg = AudioSegment.from_file(path)
        pydub_play(seg)
    elif PLAYSOUND_AVAILABLE:
        playsound(path)
    else:
        print("No audio backend installed.")
