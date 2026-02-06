# AGI Robot Web Application - Quick Start Guide

## Local Development

### Prerequisites
- Node.js 18+
- MongoDB running (or use Docker Compose)

### Option 1: Docker Compose (Recommended)

Start all services with one command:

```bash
cd web
docker-compose up -d
```

This starts:
- MongoDB on port 27017 (internal)
- Backend API on port 3000
- Frontend on port 80

Access:
- Frontend: http://localhost
- Dashboard: http://localhost/dashboard  
- API: http://localhost:3000/api/health

### Option 2: Manual Development Mode

**Terminal 1 - Backend**:
```bash
cd web/backend
npm install
cp .env.example .env
npm run dev
```

**Terminal 2 - Frontend**:
```bash
cd web
npm install
npm run dev
```

Access:
- Frontend: http://localhost:5173
- Dashboard: http://localhost:5173/dashboard
- API: http://localhost:3000/api/health

## Features

### Landing Page (/)
- Stunning glassmorphism design
- Project features showcase
- Technical specifications
- Cost breakdown table
- Call-to-action to dashboard

### Dashboard (/dashboard)
- **Live Telemetry**: Distance, temperature, humidity
- **Movement Controls**: Forward, back, left, right, stop
- **Robot Modes**: AGI, Panic, ASI toggles
- **Speed Display**: Current RPM with progress bar
- **Real-time Updates**: Socket.IO connection

## API Endpoints

### Control
- `POST /api/control/move` - Move robot
- `POST /api/control/agi` - Toggle AGI mode
- `POST /api/control/panic` - Toggle panic mode
- `POST /api/control/rgb` - Set LED color
- `POST /api/control/arm` - Set arm positions

### Data
- `GET /api/state` - Current robot state
- `POST /api/state` - Update state
- `GET /api/telemetry` - Historical telemetry
- `GET /api/logs/commands` - Command history

## Deployment

### GitHub Actions
Push to `main` branch:
```bash
git add .
git commit -m "Deploy updates"
git push origin main
```

Automatically deploys to robot.mvpgen.com via Docker Compose.

### Manual VPS Deployment

On VPS:
```bash
cd /var/www/agi-robot
docker-compose pull
docker-compose build
docker-compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete setup guide.

## Testing the Dashboard

1. **Start Backend**: Ensure MongoDB and backend are running
2. **Start Frontend**: Access http://localhost:5173/dashboard
3. **Check Connection**: Green indicator = Socket.IO connected
4. **Try Controls**: 
   - Click movement buttons (Forward, Back, Left, Right)
   - Toggle AGI or Panic modes
   - Watch telemetry update in real-time

## Troubleshooting

### "Cannot connect to backend"
- Check backend is running: `npm run dev` in `web/backend/`
- Verify MongoDB is running: `docker ps` or `systemctl status mongod`
- Check API URL in `.env`: `VITE_API_URL=http://localhost:3000`

### "Socket.IO disconnected"
- Backend must be running for WebSocket connection
- Check browser console for errors
- Verify CORS settings in backend `.env`

### Frontend won't start
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`

## Project Structure

```
web/
├── src/
│   ├── pages/
│   │   ├── LandingPage.jsx        # Home page
│   │   ├── Dashboard.jsx          # Control dashboard
│   │   └── *.css
│   ├── components/
│   │   ├── TelemetryCard.jsx      # Telemetry display
│   │   ├── ControlButton.jsx      # Interactive buttons
│   │   └── *.css
│   ├── services/
│   │   ├── api.js                 # Backend API calls
│   │   └── socket.js              # Socket.IO service
│   ├── App.jsx                    # Router configuration
│   └── index.css                  # Design system
├── backend/
│   ├── models/                    # MongoDB schemas
│   ├── routes/                    # API routes
│   ├── server.js                  # Express + Socket.IO
│   └── package.json
├── docker-compose.yml             # Multi-container setup
└── package.json
```

## Next Steps

- Test robot integration with Python `main.py`
- Add camera feed viewer
- Implement settings panel
- Build spatial map visualization
- Add movement history timeline

## License

MIT
