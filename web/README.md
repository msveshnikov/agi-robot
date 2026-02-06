# AGI Robot Web Application

Complete web interface for the AGI Robot project with React frontend, Node.js backend, and MongoDB database.

## Project Structure

```
web/
├── frontend files (React + Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   └── LandingPage.css
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/
│   │   └── (robot images)
│   ├── index.html
│   ├── package.json
│   ├── Dockerfile                  # Frontend multi-stage build
│   └── nginx.conf                  # Nginx config for frontend
├── backend/
│   ├── models/
│   │   ├── RobotState.js           # Robot state schema
│   │   ├── TelemetryLog.js         # Telemetry logging
│   │   └── CommandLog.js           # Command audit trail
│   ├── routes/
│   │   └── api.js                  # REST API endpoints
│   ├── server.js                   # Express server + Socket.IO
│   ├── package.json
│   ├── Dockerfile                  # Backend Node.js image
│   ├── .env.example
│   ├── .env                        # Local development
│   ├── .env.production             # Docker production
│   └── README.md
├── docker-compose.yml              # Multi-container orchestration
└── DEPLOYMENT.md                   # Deployment guide
```

## Features

### Frontend
- 🎨 Stunning landing page with glassmorphism design
- ⚡ React 18 with Vite for fast development
- 🎭 Framer Motion animations
- 📱 Responsive design (mobile, tablet, desktop)
- 🎯 Lucide React icons

### Backend
- 🚀 Express.js REST API
- 📊 MongoDB with Mongoose ODM
- 🔄 Socket.IO for real-time updates
- 📝 Command and telemetry logging
- 🏥 Health checks

### Deployment
- 🐳 Docker Compose orchestration
- 📦 Multi-stage builds for optimization
- 🔄 GitHub Actions CI/CD
- 🌐 Automated deployment to robot.mvpgen.com

## Quick Start

### Local Development

**Prerequisites**: Node.js 18+, MongoDB (or use Docker Compose)

```bash
# Clone repository
git clone https://github.com/msveshnikov/Arduino.git
cd Arduino/web

# Start with Docker Compose (recommended)
docker-compose up -d

# OR run manually:

# Terminal 1 - Backend
cd backend
npm install
cp .env.example .env
npm run dev

# Terminal 2 - Frontend
cd ..
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:5173
- Backend API: http://localhost:3000/api/health

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Docker Compose deployment guide.

```bash
# On VPS
cd /var/www/agi-robot
docker-compose up -d
```

## Technology Stack

**Frontend**
- React 18
- Vite
- React Router DOM
- Framer Motion
- Lucide React
- Axios
- Socket.IO Client

**Backend**
- Node.js 20
- Express.js
- MongoDB + Mongoose
- Socket.IO
- CORS
- Morgan (logging)

**DevOps**
- Docker & Docker Compose
- GitHub Actions
- Nginx (frontend server)

## Environment Variables

### Backend (.env)

```env
MONGODB_URI=mongodb://localhost:27017/agi-robot
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
PYTHON_MEDIA_SERVICE_URL=http://localhost:5000
```

### Docker Production (.env.production)

```env
MONGODB_URI=mongodb://mongodb:27017/agi-robot
PORT=3000
NODE_ENV=production
CORS_ORIGIN=https://robot.mvpgen.com
PYTHON_MEDIA_SERVICE_URL=http://host.docker.internal:5000
```

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild
docker-compose build --no-cache

# Check status
docker-compose ps
```

## Development

### Frontend Development

```bash
cd web
npm install
npm run dev        # Development server
npm run build      # Production build
npm run preview    # Preview production build
```

### Backend Development

```bash
cd web/backend
npm install
npm run dev        # Development with auto-reload
npm start          # Production mode
```

## API Documentation

See [backend/README.md](backend/README.md) for complete API documentation.

### Key Endpoints

- `GET /api/state` - Current robot state
- `POST /api/state` - Update robot state
- `POST /api/control/move` - Movement commands
- `POST /api/control/agi` - Toggle AGI mode
- `POST /api/control/panic` - Emergency mode
- `GET /api/telemetry` - Historical sensor data
- `GET /api/logs/commands` - Command history

### Real-time Events (Socket.IO)

- `state` - Robot state changes
- `telemetry` - Live sensor updates
- `camera` - Camera feed

## License

MIT
