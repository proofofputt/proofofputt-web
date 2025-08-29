# Desktop Computer Vision Processing

This directory will contain the local computer vision processing components moved from the backend:

## Planned Structure:
```
python/
├── video_processor.py    # YOLOv8 golf ball detection
├── putt_classifier.py   # ROI-based putt classification  
├── run_tracker.py       # Session management & CV pipeline
├── session_reporter.py  # Statistics calculation
└── requirements.txt     # Python dependencies
```

## Future Implementation:
1. Move CV processing from backend to desktop
2. Implement Python sidecar with Tauri
3. Generate local session data (CSV format)
4. Submit processed results to backend API

## Current Status:
- Basic Rust session management implemented
- Desktop session UI components created
- CV processing still needs to be relocated from backend

This ensures privacy, performance, and offline capability for putting analysis.