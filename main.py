from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from supabase import create_client
import os
import tempfile
from dotenv import load_dotenv
from transcribe import transcribe_video, get_youtube_video_id
import re
from urllib.parse import urlencode
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Video Transit to Sign Language Research Prototype",
    description="Research prototype for analyzing YouTube video content translation to sign language using sign.mt",
    version="1.0.0"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Modify this in production
)

# Constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mpeg", "video/quicktime"]

# Initialize Supabase
SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("ANON_PUBLIC_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    BUCKET_NAME = "video-to-sign"
else:
    supabase = None
    logger.warning("Supabase credentials not found. File upload will be disabled.")

def segment_transcript(transcript: str, max_length: int = 100) -> list[str]:
    """
    Segment transcript into smaller chunks suitable for sign.mt input.
    sign.mt has word/length limitations, so we need to break down the text.
    """
    # Split by sentences first
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        # If sentence itself is too long, split by commas
        if len(sentence) > max_length:
            comma_parts = sentence.split(',')
            for part in comma_parts:
                if len(current_segment) + len(part) <= max_length:
                    current_segment += part + ","
                else:
                    if current_segment:
                        segments.append(current_segment.strip().rstrip(','))
                    current_segment = part + ","
        else:
            if len(current_segment) + len(sentence) <= max_length:
                current_segment += sentence + " "
            else:
                segments.append(current_segment.strip())
                current_segment = sentence + " "
    
    if current_segment:
        segments.append(current_segment.strip())
    
    return segments

def get_sign_mt_url(text: str) -> str:
    """Generate sign.mt URL with text parameter"""
    base_url = "https://sign.mt"
    params = {"text": text}
    return f"{base_url}?{urlencode(params)}"

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Video Transit to Sign Language Research Prototype</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container { 
                    text-align: center;
                    background-color: white;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .input-section { 
                    margin: 30px 0; 
                    padding: 20px; 
                    border: 2px dashed #ccc; 
                    border-radius: 10px;
                    background-color: #f8f9fa;
                }
                .result { 
                    margin-top: 20px; 
                    padding: 15px; 
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.05);
                }
                .segment { 
                    margin: 15px 0; 
                    padding: 15px; 
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    text-align: left;
                }
                .sign-mt-button {
                    background-color: #28a745;
                    color: white;
                    padding: 8px 15px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 10px;
                }
                .sign-mt-button:hover {
                    background-color: #218838;
                }
                input[type="text"], input[type="file"] { 
                    margin: 10px;
                    padding: 8px;
                    width: 80%;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                button { 
                    background-color: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover { 
                    background-color: #0056b3; 
                }
                .or-divider {
                    margin: 20px 0;
                    text-align: center;
                    position: relative;
                }
                .or-divider:before, .or-divider:after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    width: 45%;
                    height: 1px;
                    background-color: #ddd;
                }
                .or-divider:before { left: 0; }
                .or-divider:after { right: 0; }
                .research-notes {
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #fff3cd;
                    border-radius: 8px;
                    text-align: left;
                }
                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background-color: #f0f0f0;
                    border-radius: 10px;
                    overflow: hidden;
                    display: none;
                }
                .progress-bar-fill {
                    height: 100%;
                    background-color: #4CAF50;
                    width: 0%;
                    transition: width 0.3s ease;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎥➡️🤟 Video Transit to Sign Language</h1>
                <p>Research prototype for analyzing YouTube video content translation to sign language</p>
                
                <div class="input-section">
                    <h3>Process Video</h3>
                    
                    <!-- YouTube URL input -->
                    <form id="youtubeForm">
                        <input type="text" id="youtubeUrl" 
                               placeholder="Enter YouTube video URL (e.g., https://www.youtube.com/watch?v=...)" 
                               required>
                        <br><br>
                        <button type="submit">Process YouTube Video</button>
                    </form>

                    <div class="or-divider">OR</div>

                    <!-- File upload -->
                    <form id="uploadForm" enctype="multipart/form-data">
                        <input type="file" id="videoFile" name="file" 
                               accept="video/*" required>
                        <br><br>
                        <button type="submit">Upload & Process Video</button>
                    </form>
                </div>
                
                <div class="progress-bar" id="progressBar">
                    <div class="progress-bar-fill" id="progressBarFill"></div>
                </div>

                <div id="results" class="result" style="display: none;">
                    <h3>Sign Language Translations:</h3>
                    <div id="segments"></div>
                </div>
            </div>
            
            <script>
                // Handle YouTube form submission
                document.getElementById('youtubeForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const youtubeUrl = document.getElementById('youtubeUrl').value;
                    if (!youtubeUrl) return;
                    
                    const progressInterval = showProgress();
                    document.getElementById('results').style.display = 'none';
                    document.getElementById('segments').innerHTML = '';
                    
                    try {
                        const response = await fetch('/process-youtube/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ youtube_url: youtubeUrl })
                        });
                        
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.detail || 'Failed to process video');
                        }
                        
                        const result = await response.json();
                        
                        // Clear progress animation
                        clearInterval(progressInterval);
                        document.getElementById('progressBarFill').style.width = '100%';
                        
                        // Show results container
                        document.getElementById('results').style.display = 'block';
                        
                        // Display segmented transcripts with direct sign.mt links
                        const segmentsHtml = result.segments.map((segment, index) => {
                            const signMtUrl = 'https://sign.mt?' + new URLSearchParams({text: segment}).toString();
                            return `
                                <div class="segment">
                                    <strong>Segment ${index + 1}:</strong><br>
                                    ${segment}<br>
                                    <a href="${signMtUrl}" target="_blank" class="sign-mt-button">
                                        View Sign Language Translation ↗️
                                    </a>
                                </div>
                            `;
                        }).join('');
                        
                        document.getElementById('segments').innerHTML = segmentsHtml;
                            
                        // Hide progress bar after completion
                        setTimeout(() => {
                            document.getElementById('progressBar').style.display = 'none';
                        }, 1000);
                        
                    } catch (error) {
                        clearInterval(progressInterval);
                        document.getElementById('progressBar').style.display = 'none';
                        document.getElementById('results').style.display = 'block';
                        document.getElementById('segments').innerHTML = 
                            '<p style="color: red;">Error: ' + error.message + '</p>';
                    }
                });

                // Handle file upload form submission
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const fileInput = document.getElementById('videoFile');
                    const file = fileInput.files[0];
                    if (!file) return;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const progressInterval = showProgress();
                    document.getElementById('results').style.display = 'none';
                    document.getElementById('segments').innerHTML = '';
                    
                    try {
                        const response = await fetch('/process-video/', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.detail || 'Failed to process video');
                        }
                        
                        const result = await response.json();
                        
                        // Clear progress animation
                        clearInterval(progressInterval);
                        document.getElementById('progressBarFill').style.width = '100%';
                        
                        // Show results container
                        document.getElementById('results').style.display = 'block';
                        
                        // Display segmented transcripts with direct sign.mt links
                        const segmentsHtml = result.segments.map((segment, index) => {
                            const signMtUrl = 'https://sign.mt?' + new URLSearchParams({text: segment}).toString();
                            return `
                                <div class="segment">
                                    <strong>Segment ${index + 1}:</strong><br>
                                    ${segment}<br>
                                    <a href="${signMtUrl}" target="_blank" class="sign-mt-button">
                                        View Sign Language Translation ↗️
                                    </a>
                                </div>
                            `;
                        }).join('');
                        
                        document.getElementById('segments').innerHTML = segmentsHtml;
                            
                        // Hide progress bar after completion
                        setTimeout(() => {
                            document.getElementById('progressBar').style.display = 'none';
                        }, 1000);
                        
                    } catch (error) {
                        clearInterval(progressInterval);
                        document.getElementById('progressBar').style.display = 'none';
                        document.getElementById('results').style.display = 'block';
                        document.getElementById('segments').innerHTML = 
                            '<p style="color: red;">Error: ' + error.message + '</p>';
                    }
                });

                function showProgress() {
                    const progressBar = document.getElementById('progressBar');
                    const progressBarFill = document.getElementById('progressBarFill');
                    
                    progressBar.style.display = 'block';
                    progressBarFill.style.width = '0%';
                    
                    // Simulate progress
                    let progress = 0;
                    const interval = setInterval(() => {
                        progress += 1;
                        if (progress <= 90) {
                            progressBarFill.style.width = progress + '%';
                        }
                    }, 500);
                    
                    return interval;
                }
            </script>
        </body>
    </html>
    """

@app.post("/upload-video/")
@limiter.limit("10/minute")
async def upload_video(request: Request, file: UploadFile = File(...)):
    """
    Upload a video file to Supabase storage.
    Rate limited to 10 requests per minute.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    chunks = []
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 100MB)")
        chunks.append(chunk)
    
    # Validate file type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    
    try:
        # Combine chunks and upload
        video_data = b''.join(chunks)
        response = supabase.storage.from_(BUCKET_NAME).upload(file.filename, video_data)
        
        if hasattr(response, "error") and response.error:
            logger.error(f"Supabase upload error: {response.error}")
            raise HTTPException(status_code=400, detail=response.error.message)


        # Generate public URL
        
        # Generate public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file.filename}"
        logger.info(f"Successfully uploaded file: {file.filename}")
        
        return {"filename": file.filename, "url": public_url, "message": "Video uploaded to Supabase!"}
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/transcribe-video/")
async def transcribe_video_endpoint(file: UploadFile = File(...)):
    """Transcribe video without uploading to Supabase"""
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Transcribe the video
        transcription = transcribe_video(temp_file_path)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return {"transcription": transcription, "filename": file.filename}
    
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/process-youtube/")
@limiter.limit("5/minute")
async def process_youtube(request: Request, youtube_url: dict):
    """
    Process a YouTube video URL.
    Rate limited to 5 requests per minute.
    """
    try:
        url = youtube_url.get('youtube_url')
        if not url:
            raise HTTPException(status_code=400, detail="YouTube URL is required")
        
        logger.info(f"Processing YouTube URL: {url}")
        
        try:
            transcription = transcribe_video(url)
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        segments = segment_transcript(transcription)
        logger.info(f"Successfully processed YouTube video: {url}")
        
        return {
            "transcription": transcription,
            "segments": segments,
            "youtube_url": url
        }
    
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-video/")
@limiter.limit("5/minute")
async def process_video(request: Request, file: UploadFile = File(...)):
    """
    Process an uploaded video file.
    Rate limited to 5 requests per minute.
    """
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=415, detail="File must be a video")
    
    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    temp_file_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file_path = temp_file.name
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large (max 100MB)")
                temp_file.write(chunk)
        
        logger.info(f"Processing video file: {file.filename}")
        transcription = transcribe_video(temp_file_path)
        segments = segment_transcript(transcription)
        
        result = {
            "transcription": transcription,
            "segments": segments,
            "filename": file.filename
        }
        
        if supabase:
            try:
                file.file.seek(0)
                upload_result = await upload_video(file)
                result["upload_result"] = upload_result
            except Exception as upload_error:
                logger.warning(f"Upload to Supabase failed: {str(upload_error)}")
                result["upload_error"] = str(upload_error)
        
        logger.info(f"Successfully processed video: {file.filename}")
        return result
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.debug(f"Cleaned up temporary file: {temp_file_path}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "supabase_configured": supabase is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)