from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from supabase import create_client
import os
import tempfile
from dotenv import load_dotenv
from transcribe import transcribe_video

load_dotenv()

app = FastAPI(
    title="Video Transit to Sign Language",
    description="Research prototype for translating videos to sign language",
    version="1.0.0"
)

# Initialize Supabase
SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("ANON_PUBLIC_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    BUCKET_NAME = "video-to-sign"
else:
    supabase = None
    print("Warning: Supabase credentials not found. File upload will be disabled.")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Video Transit to Sign Language</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { text-align: center; }
                .upload-section { margin: 30px 0; padding: 20px; border: 2px dashed #ccc; border-radius: 10px; }
                .result { margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }
                input[type="file"] { margin: 10px; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎥➡️🤟 Video Transit to Sign Language</h1>
                <p>Research prototype for translating English video content to sign language</p>
                
                <div class="upload-section">
                    <h3>Upload Video for Processing</h3>
                    <form id="uploadForm" enctype="multipart/form-data">
                        <input type="file" id="videoFile" name="file" accept="video/*" required>
                        <br><br>
                        <button type="submit">Upload & Process Video</button>
                    </form>
                </div>
                
                <div id="results" class="result" style="display: none;">
                    <h3>Results:</h3>
                    <div id="transcription"></div>
                    <div id="uploadResult"></div>
                </div>
            </div>
            
            <script>
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const fileInput = document.getElementById('videoFile');
                    const file = fileInput.files[0];
                    if (!file) return;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        document.getElementById('results').style.display = 'block';
                        document.getElementById('transcription').innerHTML = '<p>Processing video... This may take a few minutes.</p>';
                        
                        const response = await fetch('/process-video/', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            document.getElementById('transcription').innerHTML = 
                                '<h4>Transcription:</h4><p>' + result.transcription + '</p>';
                            
                            if (result.upload_result) {
                                document.getElementById('uploadResult').innerHTML = 
                                    '<h4>Upload Result:</h4><p>File uploaded successfully!</p><a href="' + 
                                    result.upload_result.url + '" target="_blank">View uploaded video</a>';
                            }
                        } else {
                            document.getElementById('transcription').innerHTML = 
                                '<p style="color: red;">Error: ' + result.detail + '</p>';
                        }
                    } catch (error) {
                        document.getElementById('transcription').innerHTML = 
                            '<p style="color: red;">Error processing video: ' + error.message + '</p>';
                    }
                });
            </script>
        </body>
    </html>
    """

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        video_data = await file.read()
        
        # Upload file to Supabase Storage
        response = supabase.storage.from_(BUCKET_NAME).upload(file.filename, video_data)

        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=400, detail=response.error.message)

        # Generate public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file.filename}"

        return {"filename": file.filename, "url": public_url, "message": "Video uploaded to Supabase!"}
    
    except Exception as e:
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

@app.post("/process-video/")
async def process_video(file: UploadFile = File(...)):
    """Complete pipeline: transcribe video and optionally upload to Supabase"""
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
        
        result = {
            "transcription": transcription,
            "filename": file.filename
        }
        
        # Upload to Supabase if configured
        if supabase:
            try:
                # Reset file position for upload
                file.file.seek(0)
                upload_result = await upload_video(file)
                result["upload_result"] = upload_result
            except Exception as upload_error:
                result["upload_error"] = str(upload_error)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return result
    
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "supabase_configured": supabase is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)