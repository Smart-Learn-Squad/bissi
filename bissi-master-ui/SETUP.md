# BISSI Master - Setup Guide

## Quick Start

### Prerequisites
1. **Node.js 16+** - [Download Node.js](https://nodejs.org/)
2. **Python 3.8+** - Required for the backend
3. **Ollama** - For local AI models
4. **Git** - For version control

### Installation Steps

#### 1. Install Ollama
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

#### 2. Install a Model
```bash
# Install Gemma 2B (lightweight, good for testing)
ollama pull gemma2:2b

# Or install a larger model for better performance
ollama pull gemma2:9b

# List installed models
ollama list
```

#### 3. Start Ollama
```bash
ollama serve
```

#### 4. Setup Python Backend
```bash
cd /home/samuel-yevi/Dev/Hackathons/gemma4good/bissi

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Start the backend
python main.py
```

#### 5. Setup Electron Frontend
```bash
cd bissi-master-ui

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

### Development Workflow

#### Easy Development Start
Use the provided development script:
```bash
cd bissi-master-ui
./start-dev.sh
```
This will:
1. Start the Python backend
2. Wait for it to be ready
3. Launch the Electron app
4. Clean up when you close the app

#### Manual Development
1. Terminal 1: `python main.py` (from root directory)
2. Terminal 2: `npm start` (from bissi-master-ui directory)

### Building for Production

#### Quick Build
```bash
cd bissi-master-ui
./build.sh
```

#### Platform-Specific Builds
```bash
# Windows
npm run build-win

# Linux
npm run build-linux

# All platforms
npm run build
```

The built applications will be in the `dist/` directory.

## Configuration

### Backend Configuration
The backend runs on `http://localhost:8765` by default. Key endpoints:
- Health check: `GET /health`
- Chat: `POST /chat` + SSE on `/chat/stream`
- Models: `GET /tools`, `GET /health` (returns active model)
- Conversations: `GET /conversations`, `GET /conversations/{id}/history`

### Frontend Configuration
The Electron app connects to:
- Backend: `localhost:8765`
- Ollama: `localhost:11434`

### Profile Storage
User profiles are stored in `~/.bissi/profile.json`:
```json
{
  "first_name": "Sam",
  "last_name": "Yevi", 
  "created_at": "2026-05-06T15:08:00.000Z",
  "language": "fr"
}
```

## Troubleshooting

### Common Issues

#### "Backend non disponible" Error
**Solution**: Make sure the Python backend is running before starting Electron:
```bash
# Check if backend is running
curl http://localhost:8765/health

# If not, start it:
python main.py
```

#### Models Not Loading
**Solution**: Ensure Ollama is running and has models installed:
```bash
# Check Ollama status
ollama list

# Start Ollama if not running
ollama serve

# Install a model
ollama pull gemma2:2b
```

#### Profile Issues
**Solution**: Check the profile file:
```bash
# Check if profile exists
ls ~/.bissi/profile.json

# View profile content
cat ~/.bissi/profile.json
```

#### Electron Won't Start
**Solution**: Check Node.js and dependencies:
```bash
# Check Node.js version
node --version  # Should be 16+

# Reinstall dependencies
npm install

# Clear npm cache if needed
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Debug Mode

#### Enable DevTools
Set environment variable before starting:
```bash
NODE_ENV=development npm start
```

#### Backend Debugging
The Python backend logs to console. For more verbose logging:
```bash
python main.py --verbose
```

## Features Overview

### UI Features
- **Liquid Glass Design**: Modern glassmorphism UI with blur effects
- **Dark/Light Theme**: Toggle between themes with the moon/sun button
- **Responsive Layout**: Adapts to different window sizes
- **Smooth Animations**: CSS transitions and keyframe animations

### Chat Features
- **Real-time Streaming**: SSE-based message streaming
- **Thinking Mode**: Toggle to see AI reasoning process
- **Tool Traces**: Visual feedback for file operations
- **Model Selection**: Dynamic model switching from Ollama
- **Conversation History**: Persistent chat sessions

### Document Features
- **Canvas Viewer**: Integrated document viewing sidebar
- **Multiple Formats**: DOCX, XLSX, PDF, code files
- **Tabbed Interface**: Document/Data/Code tabs
- **Interactive Elements**: Clickable document references

### Security Features
- **Context Isolation**: Secure renderer process
- **No Node Integration**: Prevents direct system access
- **Preload Bridge**: Secure IPC communication
- **Local Only**: No internet connectivity required

## Development Tips

### Adding New Features
1. **Backend**: Add endpoints to `main.py`
2. **Frontend**: Update `preload.js` for new APIs
3. **UI**: Modify HTML/CSS in renderer files
4. **Testing**: Use development mode with DevTools

### Customizing UI
Edit CSS variables in the HTML files:
```css
:root {
  --acc: #7C3AED;      /* Accent color */
  --text: #E2E8F0;     /* Text color */
  --muted: rgba(148,163,184,0.75); /* Muted text */
  --glass: rgba(255,255,255,0.05);   /* Glass background */
  /* ... more variables */
}
```

### Adding Document Support
1. Install npm libraries in `package.json`
2. Add viewer logic to `chat.html` canvas functions
3. Update file type detection and rendering

## Support

For issues and questions:
1. Check this troubleshooting guide
2. Review the README.md file
3. Check the console logs in development mode
4. Verify all prerequisites are installed
