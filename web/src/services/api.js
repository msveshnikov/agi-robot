import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
    baseURL: `${API_BASE_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// State Management
export const fetchState = async () => {
    const response = await api.get('/state');
    return response.data;
};

export const updateState = async (data) => {
    const response = await api.post('/state', data);
    return response.data;
};

// Control Commands
export const sendMoveCommand = async (direction, distance_cm, angle_deg, speed) => {
    const response = await api.post('/control/move', {
        direction,
        distance_cm,
        angle_deg,
        speed,
    });
    return response.data;
};

export const toggleAGI = async (enabled) => {
    const response = await api.post('/control/agi', { enabled });
    return response.data;
};

export const togglePanic = async (enabled) => {
    const response = await api.post('/control/panic', { enabled });
    return response.data;
};

export const updateRGB = async (hue, sat, bri, swi) => {
    const response = await api.post('/control/rgb', { hue, sat, bri, swi });
    return response.data;
};

export const updateArm = async (arm1, arm2) => {
    const response = await api.post('/control/arm', { arm1, arm2 });
    return response.data;
};

// Data Retrieval
export const fetchTelemetry = async (params = {}) => {
    const response = await api.get('/telemetry', { params });
    return response.data;
};

export const fetchCommandLogs = async (params = {}) => {
    const response = await api.get('/logs/commands', { params });
    return response.data;
};

export const fetchCognitiveLogs = async (params = {}) => {
    const response = await api.get('/logs/cognitive', { params });
    return response.data;
};

// Text-to-Speech
export const speak = async (text, lang = 'en') => {
    const response = await api.post('/speak', { text, lang });
    return response.data;
};

// Health Check
export const checkHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

export const fetchBlogPosts = async (params = {}) => {
    const response = await api.get('/blog', { params });
    return response.data;
};

export default api;
