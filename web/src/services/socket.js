import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';

class SocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Map();
    }

    connect() {
        if (this.socket?.connected) {
            return this.socket;
        }

        this.socket = io(SOCKET_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
        });

        this.socket.on('connect', () => {
            console.log('✅ Socket.IO connected:', this.socket.id);
        });

        this.socket.on('disconnect', () => {
            console.log('🔌 Socket.IO disconnected');
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ Socket.IO connection error:', error);
        });

        // Restore event listeners
        this.listeners.forEach((callback, event) => {
            this.socket.on(event, callback);
        });

        return this.socket;
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }

    on(event, callback) {
        if (!this.socket) {
            this.connect();
        }

        this.listeners.set(event, callback);
        this.socket.on(event, callback);
    }

    off(event) {
        if (this.socket) {
            this.socket.off(event);
        }
        this.listeners.delete(event);
    }

    emit(event, data) {
        if (this.socket?.connected) {
            this.socket.emit(event, data);
        }
    }

    isConnected() {
        return this.socket?.connected || false;
    }
}

const socketService = new SocketService();

export default socketService;
