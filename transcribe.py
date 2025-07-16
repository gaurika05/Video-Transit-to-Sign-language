import whisper
import ffmpeg
import os
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import yt_dlp

def get_youtube_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    return None

def download_youtube_audio(url: str, output_path: str = "temp_audio.wav"):
    """Download audio from YouTube video"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': output_path.replace('.wav', ''),
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def get_youtube_transcript(url: str) -> str:
    """Get transcript from YouTube video"""
    try:
        video_id = get_youtube_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find any English variant
        try:
            # Try to get any English transcript (manual or auto-generated)
            transcript = None
            for lang_code in ['en-GB', 'en-US', 'en']:
                try:
                    transcript = transcript_list.find_transcript([lang_code])
                    break
                except:
                    continue
            
            if not transcript:
                raise Exception("No English transcript available for this video")
            
            # Fetch the transcript
            transcript_data = transcript.fetch()
            return ' '.join(item.text for item in transcript_data)
            
        except Exception as inner_e:
            raise Exception(f"No English transcript found: {str(inner_e)}")
        
    except Exception as e:
        raise Exception(f"Failed to get YouTube transcript: {str(e)}")

def transcribe_video(video_path: str, audio_path: str = "temp_audio.wav") -> str:
    """
    Extract audio from video and transcribe it using Whisper.
    For YouTube videos, tries to get transcript first, falls back to Whisper if no transcript available.
    """
    # Check if it's a YouTube URL
    if video_path.startswith(('http://', 'https://')):
        try:
            return get_youtube_transcript(video_path)
        except Exception as e:
            print(f"YouTube transcript not available, falling back to Whisper: {str(e)}")
            try:
                # Download audio from YouTube
                download_youtube_audio(video_path, audio_path)
                # Transcribe with Whisper
                model = whisper.load_model("base")
                transcription = model.transcribe(audio_path)
                return transcription["text"]
            finally:
                # Clean up temporary audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
    
    # Regular video file processing
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Extract audio from video
    ffmpeg.input(video_path).output(audio_path, format="wav").run(overwrite_output=True, quiet=True)

    try:
        # Load Whisper model and transcribe
        model = whisper.load_model("base")
        transcription = model.transcribe(audio_path)
        return transcription["text"]
    finally:
        # Clean up temporary audio file
        if os.path.exists(audio_path) and audio_path.startswith("temp_"):
            os.remove(audio_path)

if __name__ == "__main__":
    # For testing purposes
    video_path = "videoplayback.mp4"
    if os.path.exists(video_path):
        result = transcribe_video(video_path)
        print("Extracted Transcript: \n", result)
    else:
        print("No test video file found")