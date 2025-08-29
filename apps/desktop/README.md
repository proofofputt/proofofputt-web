# 🖥️ Proof of Putt Desktop Application

**Private Repository - Desktop Computer Vision Application**

## 🎯 Overview

The Proof of Putt desktop application provides real-time computer vision analysis for golf putting sessions. Built with Tauri and React, it captures video from your camera, processes frames using YOLO object detection, and provides detailed putting analytics.

### Key Features

- **🎥 Real-time Video Processing** - Camera capture and frame analysis
- **🤖 YOLO Object Detection** - Custom-trained model for golf ball tracking
- **📊 Session Analytics** - Detailed putting statistics and performance tracking
- **🔄 Cloud Sync** - Automatic synchronization with web platform
- **⚙️ Interactive Calibration** - ROI setup and camera configuration

## 🏗️ Technical Architecture

```
Desktop App
├── src/                    # React frontend components
│   ├── DesktopSession.jsx  # Main session interface
│   └── DesktopAnalytics.jsx # Analytics dashboard
├── src-tauri/              # Rust backend
│   ├── src/
│   │   ├── main.rs         # Application entry point
│   │   ├── api_client.rs   # Backend API communication
│   │   ├── session_data.rs # Data structures
│   │   └── session_manager.rs # Session management
│   └── tauri.conf.json     # Tauri configuration
└── python/cv_tracker/      # Python computer vision modules
    ├── calibration.py      # ROI calibration system
    ├── video_processor.py  # Frame processing pipeline
    ├── putt_classifier.py  # Ball detection and classification
    └── models/             # YOLO model files
```

## 🚀 Getting Started

### Prerequisites

- **Rust** 1.70+ with Cargo
- **Node.js** 18+ with npm
- **Python** 3.9+ with pip
- **Tauri CLI** (`cargo install tauri-cli`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/proofofputt/desktop.git
   cd desktop
   ```

2. **Install dependencies**
   ```bash
   # Install Node.js dependencies
   npm install
   
   # Install Python dependencies
   cd python/cv_tracker
   pip install -r requirements.txt
   cd ../..
   ```

3. **Development mode**
   ```bash
   npm run tauri dev
   ```

4. **Production build**
   ```bash
   npm run tauri build
   ```

## 🎮 Computer Vision System

### Calibration Process

1. **Launch calibration mode** in the desktop app
2. **Position your camera** to capture the putting area
3. **Define ROI (Region of Interest)** by clicking points around the target area
4. **Save calibration** for consistent session tracking

### Session Tracking

- **Automatic ball detection** using custom YOLO model
- **Make/miss classification** based on ball trajectory
- **Real-time statistics** updated during putting sessions
- **Performance analytics** with streak tracking and improvement metrics

## 🔧 Configuration

### API Connection

Configure the backend API endpoint in your environment:

```bash
# .env.local
VITE_API_BASE_URL=https://your-api-domain.com
# or for local development
VITE_API_BASE_URL=http://localhost:5001
```

### Camera Settings

The app automatically detects available cameras. You can specify a preferred camera in the settings interface.

## 📊 Features

### Session Management
- Start/stop putting sessions
- Real-time putt counting
- Automatic session saving
- Cloud synchronization

### Analytics Dashboard
- Session history and trends
- Performance improvement tracking
- Detailed statistics by distance/category
- Export capabilities

### Calibration Tools
- Interactive ROI definition
- Camera positioning assistance
- Lighting condition optimization
- Multiple setup profiles

## 🔐 Security & Privacy

- **Local Processing** - Computer vision runs entirely on your device
- **Secure API** - Encrypted communication with backend
- **Data Privacy** - Video never leaves your device
- **User Control** - Full control over data sharing and storage

## 🛠️ Development

### Code Structure

- **React Components** - Modern functional components with hooks
- **Rust Backend** - High-performance Tauri backend for system integration
- **Python CV** - Computer vision processing with OpenCV and YOLO
- **TypeScript** - Full type safety for frontend code

### Testing

```bash
# Run frontend tests
npm test

# Run Rust tests
cd src-tauri && cargo test

# Run Python tests
cd python/cv_tracker && python -m pytest
```

## 📱 Distribution

### Desktop Platforms

- **macOS** - `.dmg` installer and Mac App Store
- **Windows** - `.exe` installer and Microsoft Store
- **Linux** - `.AppImage` and various package formats

### Automatic Updates

The app includes automatic update functionality through Tauri's built-in updater system.

## 🤝 Contributing

This is a private repository. For contribution guidelines and development setup, please refer to the developer onboarding documentation.

## 📞 Support

For technical support or bug reports, please contact the development team through the appropriate channels.

---

## 🎯 Roadmap

- [ ] Enhanced computer vision accuracy
- [ ] Multi-camera support
- [ ] Advanced analytics and coaching features
- [ ] Integration with golf simulators
- [ ] Mobile companion app

---

**Built with ❤️ for golfers who want to improve their putting game**