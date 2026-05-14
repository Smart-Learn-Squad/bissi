# BISSI Master - Desktop Application

BISSI Master is a local AI assistant desktop application built with Electron, featuring a beautiful liquid glass UI and offline functionality.

## Screenshots

### Dark mode
![BISSI dark mode](../bissi_dark.png)

### Light mode
![BISSI light mode](../bissi-light.png)

## Features

- **Local AI Assistant**: Works completely offline with your local models
- **Liquid Glass UI**: Modern, beautiful interface with glass morphism effects
- **Document Analysis**: Support for DOCX, XLSX, PDF, and code files
- **Real-time Chat**: SSE-based streaming chat with thinking mode
- **Profile Management**: User onboarding and profile persistence
- **Model Selection**: Dynamic model loading from Ollama
- **Conversation History**: Persistent chat history with conversation management
- **Canvas Viewer**: Integrated document viewer with multiple tabs

## Requirements

- Node.js 16+
- Python 3.8+ (for backend)
- Ollama (for local models)
- Electron (installed via npm)

## Installation

1. **Install dependencies**:

   ```bash
      cd bissi-master-ui
      npm install
   ```

2. **Start the backend**:

   ```bash
   cd ..
   python main.py
   ```

3. **Start the Electron app**:

   ```bash
   cd bissi-master-ui
   npm start
   ```

## Development

### Available Scripts

- `npm start` - Start the Electron app in development mode
- `npm run build` - Build the application for production
- `npm run build-win` - Build Windows executable
- `npm run build-linux` - Build Linux packages

### Project Structure

```tree
bissi-master-ui/
├── main.js          # Main Electron process
├── preload.js       # Secure bridge between main and renderer
├── package.json     # Dependencies and build configuration
├── renderer/
│   ├── onboarding.html  # User onboarding page
│   ├── chat.html         # Main chat interface
│   └── assets/
│       └── fonts/        # Custom fonts
└── README.md
```

## Configuration

### Profile Storage

User profiles are stored in `~/.bissi/profile.json` with the following structure:

```json
{
  "first_name": "Sam",
  "last_name": "Yevi",
  "created_at": "2026-05-06T15:08:00.000Z",
  "language": "fr"
}
```

### Backend Integration

The app communicates with a FastAPI backend running on `localhost:8765`:

- Health check: `GET /health`
- Chat: `POST /chat` + SSE streaming on `/chat/stream`
- Conversations: `GET /conversations`, `GET /conversations/{id}/history`
- Tools: `GET /tools`

### Ollama Integration

Local models are loaded from Ollama running on `localhost:11434`:

- Model list: `GET /api/tags`

## UI Features

### Liquid Glass Design

- Glass morphism effects with backdrop filters
- Smooth animations and transitions
- Dark/light theme support
- CSS variables for easy customization

### Chat Interface

- Real-time message streaming
- Tool execution traces
- Thinking mode toggle
- Model selection dropdown
- Conversation history sidebar

### Canvas Viewer

- Multi-tab document viewing (Document/Data/Code)
- DOCX rendering via mammoth.js
- XLSX table display via SheetJS
- PDF viewing via pdfjs-dist
- Code syntax highlighting

## Building for Production

### Windows

```bash
npm run build-win
```

Creates an NSIS installer in `dist/`.

### Linux

```bash
npm run build-linux
```

Creates AppImage and deb packages in `dist/`.

## Security

- Context isolation enabled
- Node integration disabled in renderer
- Secure preload bridge for IPC communication
- No direct file system access from renderer

## Troubleshooting

### Backend Not Available

If you see "Backend non disponible — Lancez main.py":

1. Ensure the Python backend is running on localhost:8765
2. Check that main.py is started before the Electron app
3. Verify no firewall is blocking the connection

### Models Not Loading

If models don't appear in the dropdown:

1. Ensure Ollama is running on localhost:11434
2. Check that models are installed: `ollama list`
3. Install models if needed: `ollama pull gemma:2b`

### Profile Issues

If onboarding appears every time:

1. Check that ~/.bissi/profile.json exists
2. Verify file permissions
3. Check for JSON syntax errors in the profile file

## License

MIT License - see LICENSE file for details.
