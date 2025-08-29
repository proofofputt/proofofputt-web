# 🏌️ Proof of Putt

**AI-powered golf putting training and competition platform 

[![Vercel Deployment](https://vercel.com/button)](https://vercel.com/new/clone)

## 🎯 Overview

Proof of Putt transforms putting practice into verifiable, competitive experiences through computer vision technology and decentralized competition architecture. The platform enables remote skill-based competitions with tamper-proof performance data.

### Key Features

- **🎥 Computer Vision Analysis** - YOLO-based ball tracking and putt classification
- **📊 Performance Analytics** - Detailed putting statistics and improvement tracking  
- **⚔️ Competitive Gaming** - Duels, leagues, and tournament systems
- **💰 Subscription Model** - Freemium SaaS with premium analytics

## 🏗️ Technical Architecture

### Multi-Platform System
```
Desktop App (Tauri + React)  ←→  Backend API (Flask + PostgreSQL)  ←→  Web App (React + Vite)
        ↓                                    ↓                                ↓
   Camera Capture                    Performance Data                User Interface
   Computer Vision                   User Management                  Social Features
   Session Tracking                  Competition Logic               Payment Integration
```

### Core Components

- **Backend**: Flask API with PostgreSQL, deployed on Vercel
- **Frontend**: React web application with responsive design
- **Desktop**: Tauri-based desktop app for computer vision processing
- **Database**: PostgreSQL with comprehensive user and session management
- **Deployment**: Vercel serverless with NeonDB PostgreSQL

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- Rust (for desktop app)
- PostgreSQL (local) or NeonDB (cloud)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/[username]/proof-of-putt.git
   cd proof-of-putt
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set environment variables
   export DATABASE_URL="your_postgresql_connection_string"
   export ALLOWED_ORIGINS="http://localhost:5173,https://your-domain.com"
   
   # Run the API
   python api.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend/webapp
   npm install
   npm run dev
   ```

4. **Desktop App Setup**
   ```bash
   cd desktop
   npm install
   npm run tauri dev
   ```

### Environment Variables

Create `.env` files in appropriate directories:

**Backend (.env)**
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
ALLOWED_ORIGINS=http://localhost:5173,https://your-domain.com
GEMINI_API_KEY=your_gemini_api_key_for_ai_coach
```

**Frontend (.env.local)**
```
VITE_API_BASE_URL=http://localhost:5001
VITE_APP_NAME=Proof of Putt
```

## 📁 Project Structure

```
proof-of-putt/
├── backend/                 # Flask API server
│   ├── api.py              # Main API endpoints
│   ├── data_manager.py     # Database operations
│   ├── notification_service.py
│   ├── utils.py
│   ├── requirements.txt
│   └── vercel.json         # Vercel deployment config
├── frontend/webapp/        # React web application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── context/       # React context providers
│   │   ├── pages/         # Page components
│   │   └── api.js         # API client
│   ├── package.json
│   └── vite.config.js
├── desktop/                # Tauri desktop application
│   ├── src/               # React frontend for desktop
│   ├── src-tauri/         # Rust backend for desktop
│   │   ├── src/
│   │   └── Cargo.toml
│   └── package.json
└── README.md
```

## 🔧 API Endpoints

### Authentication
- `POST /login` - User authentication
- `POST /register` - User registration
- `POST /forgot-password` - Password recovery
- `POST /reset-password` - Reset password with token

### Player Management
- `GET /player/<id>/data` - Player profile
- `GET /player/<id>/career-stats` - Career statistics
- `GET /player/<id>/sessions` - Session history

### Competition System
- `POST /duels` - Create duel challenge
- `GET /duels/list/<id>` - Player's duels
- `POST /duels/<id>/respond` - Accept/decline duel
- `POST /duels/<id>/submit` - Submit duel performance

### League System
- `GET /leagues` - Available leagues
- `POST /leagues` - Create league
- `GET /leagues/<id>` - League details
- `GET /leagues/<id>/leaderboard` - League standings

### Fundraising
- `GET /fundraisers` - Active fundraisers
- `POST /fundraisers` - Create fundraiser
- `POST /fundraisers/<id>/pledge` - Create pledge

## 🎮 Computer Vision System

The platform uses YOLO-based object detection for real-time golf ball tracking:

1. **Calibration**: Interactive ROI (Region of Interest) setup
2. **Detection**: Real-time ball tracking during putting sessions
3. **Classification**: Automatic make/miss determination
4. **Analytics**: Performance metrics and improvement tracking

### Supported Metrics
- Makes and misses by distance/category
- Consecutive makes streaks
- Putting speed and rhythm
- Session duration and intensity
- Improvement trends over time

## 💰 Business Model

### Subscription Tiers
- **Free**: Basic session tracking, limited history
- **Premium ($2/month)**: Full analytics, unlimited history, competitions
- **Enterprise**: Custom solutions for businesses and instructors

### Future Revenue Streams
- Wagering platform fees (3-5%)
- Tournament entry fees
- Charity fundraising platform
- Corporate team-building events

## 🔒 Security & Compliance

- **Data Protection**: Encrypted user data and secure authentication
- **Skill-Based Gaming**: Compliance with US skill-based gaming regulations
- **Financial Security**: Prepared for decentralized escrow integration
- **Privacy**: GDPR and CCPA compliant data handling

## 🚀 Deployment

### Vercel Deployment

1. **Connect GitHub repository to Vercel**
2. **Configure environment variables** in Vercel dashboard
3. **Set build settings**:
   - Framework Preset: `Vite`
   - Root Directory: `frontend/webapp`
   - Build Command: `npm run build`
   - Output Directory: `dist`

### Database Setup (NeonDB)

1. Create NeonDB PostgreSQL instance
2. Configure connection string in environment variables
3. Database tables are automatically created on first run

## 📊 Performance & Scaling

- **API Response Time**: <200ms average
- **Database**: Optimized queries with proper indexing
- **Frontend**: Lazy loading and code splitting
- **Desktop**: Native performance with Tauri
- **Deployment**: Serverless scaling with Vercel

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary software. All rights reserved.

## 📞 Contact

- **Website**: [https://proofofputt.com](https://proofofputt.com)
- **Email**: [contact@proofofputt.com](mailto:contact@proofofputt.com)
- **Issues**: [GitHub Issues](https://github.com/[username]/proof-of-putt/issues)

## 🎯 Roadmap

- [x] Core platform development
- [x] Computer vision integration
- [x] Web application
- [x] Desktop application
- [x] Competition system
- [x] Fundraising features
- [ ] Bitcoin wagering integration
- [ ] Mobile application
- [ ] Advanced AI coaching
- [ ] International expansion

---

**Built with ❤️ for the golf community**
