# Deployment Guide for Video Transit to Sign Language

This guide provides multiple deployment options for your research prototype.

## Environment Variables Required

Before deploying, you'll need to set up these environment variables:

```
PROJECT_URL=https://your-project.supabase.co
ANON_PUBLIC_KEY=your-anon-public-key-here
```

## Deployment Options

### 1. Render (Recommended - Free Tier Available) ⭐

1. Fork this repository to your GitHub account
2. Go to [render.com](https://render.com) and sign up
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` configuration
6. Add your environment variables in the Render dashboard
7. Deploy!

**Pros:** Easy setup, free tier, automatic deployments
**Cons:** Cold starts on free tier

### 2. Railway

1. Go to [railway.app](https://railway.app)
2. Sign up and click "Deploy from GitHub repo"
3. Select your repository
4. Railway will use the `railway.toml` configuration
5. Add environment variables in Railway dashboard
6. Deploy!

**Pros:** Fast deployment, good performance
**Cons:** Limited free tier

### 3. Heroku

1. Install the Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set environment variables:
   ```bash
   heroku config:set PROJECT_URL=your-supabase-url
   heroku config:set ANON_PUBLIC_KEY=your-supabase-key
   ```
5. Deploy: `git push heroku main`

**Pros:** Well-documented, reliable
**Cons:** No free tier anymore

### 4. Google Cloud Run (Container Deployment)

1. Build the Docker image:
   ```bash
   docker build -t video-to-sign .
   ```
2. Tag for Google Container Registry:
   ```bash
   docker tag video-to-sign gcr.io/YOUR-PROJECT-ID/video-to-sign
   ```
3. Push to registry:
   ```bash
   docker push gcr.io/YOUR-PROJECT-ID/video-to-sign
   ```
4. Deploy to Cloud Run:
   ```bash
   gcloud run deploy --image gcr.io/YOUR-PROJECT-ID/video-to-sign --platform managed
   ```

### 5. Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` file with your environment variables
3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
4. Open http://localhost:8000

## Testing the Deployment

Once deployed, your application will have:

- **Main Interface**: `https://your-app-url.com/` - Upload and process videos
- **Health Check**: `https://your-app-url.com/health` - Check if app is running
- **API Documentation**: `https://your-app-url.com/docs` - Interactive API docs

## Troubleshooting

### Common Issues:

1. **Whisper Model Download**: First video processing may take longer as Whisper downloads the model
2. **FFmpeg Issues**: Make sure ffmpeg is installed (included in Docker image)
3. **Memory Limits**: Video processing is memory-intensive; consider upgrading your plan
4. **Supabase Errors**: Verify your environment variables are correct

### Performance Optimization:

- Use smaller Whisper models for faster processing (`tiny`, `base` instead of `large`)
- Implement file size limits to prevent memory issues
- Consider using background tasks for video processing

## Sharing Your Prototype

Once deployed, you can share your research prototype by:

1. Sharing the main URL with colleagues
2. Demonstrating the video upload and transcription features
3. Using the provided test video (`videoplayback.mp4`) for demos
4. Showcasing the integration with Supabase for storage

## Next Steps

To enhance your prototype:

1. Add authentication for user management
2. Implement actual sign language translation (currently only transcription)
3. Add video processing progress indicators
4. Implement batch processing for multiple videos
5. Add support for different languages 