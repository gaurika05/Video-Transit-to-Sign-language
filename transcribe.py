import whisper
import ffmpeg
import os
video_path = "C:/ONEDRIVE MAIT/OneDrive - MAIT/Desktop/video-to-sign/videoplayback.mp4"
audio_path = "audio.wav"

if not os.path.exists(video_path):
    raise FileNotFoundError(f"Video file not found: {video_path}")

ffmpeg.input(video_path).output(audio_path, format="wav").run(overwrite_output=True)

model = whisper.load_model("base")

transcription = model.transcribe(audio_path)
print("Extracted Transcript: \n", transcription["text"])