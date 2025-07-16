import whisper
import ffmpeg
import os
from pathlib import Path

def transcribe_video(video_path: str, audio_path: str = "temp_audio.wav"):
    """
    Extract audio from video and transcribe it using Whisper
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Extract audio from video
    ffmpeg.input(video_path).output(audio_path, format="wav").run(overwrite_output=True, quiet=True)

    # Load Whisper model and transcribe
    model = whisper.load_model("base")
    transcription = model.transcribe(audio_path)
    
    # Clean up temporary audio file
    if os.path.exists(audio_path) and audio_path.startswith("temp_"):
        os.remove(audio_path)
    
    return transcription["text"]

if __name__ == "__main__":
    # For testing purposes
    video_path = "videoplayback.mp4"
    if os.path.exists(video_path):
        result = transcribe_video(video_path)
        print("Extracted Transcript: \n", result)
    else:
        print("No test video file found")