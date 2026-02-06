import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import mongoose from 'mongoose';
import cors from 'cors';
import morgan from 'morgan';
import dotenv from 'dotenv';
import apiRouter from './routes/api.js';

// Load environment variables
dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
    cors: {
        origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
        methods: ['GET', 'POST']
    }
});

const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/agi-robot';

// Middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:5173'
}));
app.use(express.json());
app.use(morgan('dev'));

// Make Socket.IO available to routes
app.set('io', io);

// MongoDB Connection
mongoose.connect(MONGODB_URI)
    .then(() => {
        console.log('✅ Connected to MongoDB');
    })
    .catch((error) => {
        console.error('❌ MongoDB connection error:', error);
        process.exit(1);
    });

// Socket.IO Connection
io.on('connection', (socket) => {
    console.log(`🔌 Client connected: ${socket.id}`);

    socket.on('disconnect', () => {
        console.log(`🔌 Client disconnected: ${socket.id}`);
    });

    // Handle camera feed (if needed)
    socket.on('camera', (data) => {
        // Broadcast camera feed to all clients
        socket.broadcast.emit('camera', data);
    });
});

// API Routes
app.use('/api', apiRouter);

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'AGI Robot API Server',
        version: '1.0.0',
        endpoints: {
            health: '/api/health',
            state: '/api/state',
            telemetry: '/api/telemetry',
            commands: '/api/logs/commands'
        }
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('❌ Error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

// Start server
httpServer.listen(PORT, () => {
    console.log(`🚀 AGI Robot Backend running on port ${PORT}`);
    console.log(`📡 Socket.IO ready for real-time communication`);
    console.log(`🌐 CORS enabled for: ${process.env.CORS_ORIGIN || 'http://localhost:5173'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, closing server...');
    httpServer.close(() => {
        mongoose.connection.close();
        console.log('Server closed');
        process.exit(0);
    });
});
