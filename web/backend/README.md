# AGI Robot Backend

Backend API server for AGI Robot control and telemetry.

## Features

- RESTful API for robot control
- Real-time telemetry via Socket.IO
- MongoDB for state and logging
- Command audit trail
- CORS-enabled for frontend integration

## Prerequisites

- Node.js 18+
- MongoDB 5.0+

## Installation

```bash
cd web/backend
npm install
```

## Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Required environment variables:
- `MONGODB_URI`: MongoDB connection string
- `PORT`: API server port (default: 3000)
- `CORS_ORIGIN`: Frontend URL for CORS
- `PYTHON_MEDIA_SERVICE_URL`: Media service endpoint

## Development

```bash
npm run dev
```

## Production

```bash
npm start
```

Or use PM2:
```bash
pm2 start server.js --name agi-robot-backend
```

## API Endpoints

### State Management
- `GET /api/state` - Get current robot state
- `POST /api/state` - Update robot state

### Control
- `POST /api/control/move` - Send movement command
- `POST /api/control/agi` - Toggle AGI mode
- `POST /api/control/panic` - Toggle panic mode
- `POST /api/control/rgb` - Update RGB LED
- `POST /api/control/arm` - Update arm positions

### Data Retrieval
- `GET /api/telemetry` - Get telemetry history
- `GET /api/logs/commands` - Get command history

### Other
- `GET /api/health` - Health check
- `POST /api/speak` - Text-to-speech

## Socket.IO Events

### Emitted by Server
- `state` - Robot state updates
- `telemetry` - Real-time telemetry data
- `camera` - Camera feed (broadcast)

### Received by Server
- `camera` - Camera feed from client

## Deployment

Automated via GitHub Actions to robot.mvpgen.com. See `.github/workflows/deploy.yml`.

## License

MIT
