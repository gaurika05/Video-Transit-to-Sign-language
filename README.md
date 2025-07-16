# 🎥➡️🤟 Video Transit to Sign Language

A research prototype that processes English video content and provides transcription as a step toward sign language translation.

## ✨ Features

- **Video Upload & Processing**: Upload video files through a modern web interface
- **Audio Transcription**: Automatic speech-to-text using OpenAI Whisper
- **Cloud Storage**: Integration with Supabase for video storage
- **REST API**: Complete FastAPI backend with interactive documentation
- **Real-time Processing**: Live feedback during video processing

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, OpenAI Whisper
- **Storage**: Supabase, PostgreSQL
- **Processing**: FFmpeg for audio extraction
- **Deployment**: Docker, Render, Railway, Heroku compatible

## 🚀 Quick Start

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/gaurika05/Video-Transit-to-Sign-language.git
   cd Video-Transit-to-Sign-language
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create `.env` file):
   ```
   PROJECT_URL=https://your-project.supabase.co
   ANON_PUBLIC_KEY=your-anon-public-key-here
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open http://localhost:8000 in your browser

### Live Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment options including Render, Railway, Heroku, and Google Cloud.

## 📖 API Documentation

Once running, visit:
- **Main Interface**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎯 Usage

1. **Upload Video**: Use the web interface to upload video files
2. **Processing**: The system extracts audio and transcribes speech
3. **Results**: View transcription results and uploaded file links
4. **Storage**: Videos are optionally stored in Supabase for later access

## 🔧 Configuration

The application requires Supabase for cloud storage but can work without it for transcription-only functionality.

Required environment variables:
- `PROJECT_URL`: Your Supabase project URL
- `ANON_PUBLIC_KEY`: Your Supabase anonymous public key

## 📝 Research Context

This prototype demonstrates the first step in video-to-sign-language translation by:
1. Processing video input
2. Extracting and transcribing audio content
3. Providing a foundation for future sign language generation

## 🤝 Contributing

This is a research prototype. Feel free to:
- Report issues
- Suggest improvements
- Fork and enhance the functionality
- Add actual sign language translation features

## 📄 License

Research prototype - see repository for licensing details.
