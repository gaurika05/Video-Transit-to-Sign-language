from fastapi import FastAPI, File, UploadFile
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initialize Supabase
SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("ANON_PUBLIC_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Name of storage bucket
BUCKET_NAME = "video-to-sign"

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    video_data = file.file.read()
    
    # Upload file to Supabase Storage
    response = supabase.storage.from_(BUCKET_NAME).upload(file.filename, video_data)

    if hasattr(response, "error") and response.error:  # Check if error attribute exists
        return {"error": response.error.message}  # Get the error message correctly

    # Generate public URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file.filename}"

    return {"filename": file.filename, "url": public_url, "message": "Video uploaded to Supabase!"}