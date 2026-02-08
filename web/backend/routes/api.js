import express from 'express';
import RobotState from '../models/RobotState.js';
import TelemetryLog from '../models/TelemetryLog.js';
import CommandLog from '../models/CommandLog.js';
import CognitiveLog from '../models/CognitiveLog.js';

const router = express.Router();

// Health check
router.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date() });
});

// Get current robot state
router.get('/state', async (req, res) => {
    try {
        let state = await RobotState.findOne().sort({ updated_at: -1 });

        // Initialize state if doesn't exist
        if (!state) {
            state = await RobotState.create({});
        }

        res.json(state);
    } catch (error) {
        console.error('Error fetching state:', error);
        res.status(500).json({ error: 'Failed to fetch robot state' });
    }
});

// Update robot state
router.post('/state', async (req, res) => {
    try {
        const updates = req.body;

        let state = await RobotState.findOne().sort({ updated_at: -1 });

        if (!state) {
            state = await RobotState.create(updates);
        } else {
            Object.assign(state, updates);
            await state.save();
        }

        // Emit updated state via Socket.IO
        req.app.get('io').emit('state', state);

        // Log telemetry if updated
        if (updates.distance !== undefined || updates.temperature !== undefined || updates.humidity !== undefined) {
            await TelemetryLog.create({
                distance: updates.distance || state.distance,
                temperature: updates.temperature || state.temperature,
                humidity: updates.humidity || state.humidity
            });

            req.app.get('io').emit('telemetry', {
                distance: state.distance,
                temperature: state.temperature,
                humidity: state.humidity,
                timestamp: new Date()
            });
        }

        // Log cognitive state if updated
        if (updates.plan !== undefined || updates.subplan !== undefined || updates.memory !== undefined || updates.goal !== undefined) {
            await CognitiveLog.create({
                plan: updates.plan || state.plan,
                subplan: updates.subplan || state.subplan,
                memory: updates.memory || state.memory,
                goal: updates.goal || state.goal
            });

            req.app.get('io').emit('cognitive', {
                plan: state.plan,
                subplan: state.subplan,
                memory: state.memory,
                goal: state.goal,
                timestamp: new Date()
            });
        }

        res.json(state);
    } catch (error) {
        console.error('Error updating state:', error);
        res.status(500).json({ error: 'Failed to update robot state' });
    }
});

// Movement control
router.post('/control/move', async (req, res) => {
    try {
        const { direction, distance_cm, angle_deg, speed } = req.body;

        // Validate command
        if (!['forward', 'back', 'left', 'right', 'stop'].includes(direction)) {
            return res.status(400).json({ error: 'Invalid direction' });
        }

        // Log command
        await CommandLog.create({
            command_type: direction === 'stop' ? 'stop' : 'move',
            command_data: { direction, distance_cm, angle_deg, speed },
            source: 'api'
        });

        // Update state
        const state = await RobotState.findOne().sort({ updated_at: -1 });
        if (state) {
            // Reset all directions
            state.forward = false;
            state.back = false;
            state.left = false;
            state.right = false;

            // Set requested direction
            if (direction !== 'stop') {
                state[direction] = true;
            }

            if (speed !== undefined) {
                state.speed = speed;
            }

            await state.save();
            req.app.get('io').emit('state', state);
        }

        res.json({ success: true, command: { direction, distance_cm, angle_deg, speed } });
    } catch (error) {
        console.error('Error sending move command:', error);
        res.status(500).json({ error: 'Failed to send move command' });
    }
});

// Toggle AGI mode
router.post('/control/agi', async (req, res) => {
    try {
        const { enabled } = req.body;

        const state = await RobotState.findOne().sort({ updated_at: -1 });
        if (state) {
            state.agi = enabled;
            await state.save();
            req.app.get('io').emit('state', state);

            await CommandLog.create({
                command_type: 'agi',
                command_data: { enabled },
                source: 'api'
            });
        }

        res.json({ success: true, agi: enabled });
    } catch (error) {
        console.error('Error toggling AGI:', error);
        res.status(500).json({ error: 'Failed to toggle AGI mode' });
    }
});

// Toggle panic mode
router.post('/control/panic', async (req, res) => {
    try {
        const { enabled } = req.body;

        const state = await RobotState.findOne().sort({ updated_at: -1 });
        if (state) {
            state.panic = enabled;
            await state.save();
            req.app.get('io').emit('state', state);

            await CommandLog.create({
                command_type: 'panic',
                command_data: { enabled },
                source: 'api'
            });
        }

        res.json({ success: true, panic: enabled });
    } catch (error) {
        console.error('Error toggling panic:', error);
        res.status(500).json({ error: 'Failed to toggle panic mode' });
    }
});

// Get telemetry history
router.get('/telemetry', async (req, res) => {
    try {
        const { limit = 100, skip = 0, from, to } = req.query;

        const query = {};
        if (from || to) {
            query.timestamp = {};
            if (from) query.timestamp.$gte = new Date(from);
            if (to) query.timestamp.$lte = new Date(to);
        }

        const logs = await TelemetryLog.find(query)
            .sort({ timestamp: -1 })
            .limit(parseInt(limit))
            .skip(parseInt(skip));

        const total = await TelemetryLog.countDocuments(query);

        res.json({ logs, total, limit: parseInt(limit), skip: parseInt(skip) });
    } catch (error) {
        console.error('Error fetching telemetry:', error);
        res.status(500).json({ error: 'Failed to fetch telemetry logs' });
    }
});

// Get command history
router.get('/logs/commands', async (req, res) => {
    try {
        const { limit = 50, skip = 0, type, source } = req.query;

        const query = {};
        if (type) query.command_type = type;
        if (source) query.source = source;

        const logs = await CommandLog.find(query)
            .sort({ timestamp: -1 })
            .limit(parseInt(limit))
            .skip(parseInt(skip));

        const total = await CommandLog.countDocuments(query);

        res.json({ logs, total, limit: parseInt(limit), skip: parseInt(skip) });
    } catch (error) {
        console.error('Error fetching command logs:', error);
        res.status(500).json({ error: 'Failed to fetch command logs' });
    }
});

// Get cognitive state history
router.get('/logs/cognitive', async (req, res) => {
    try {
        const { limit = 50, skip = 0 } = req.query;

        const logs = await CognitiveLog.find()
            .sort({ timestamp: -1 })
            .limit(parseInt(limit))
            .skip(parseInt(skip));

        const total = await CognitiveLog.countDocuments();

        res.json({ logs, total, limit: parseInt(limit), skip: parseInt(skip) });
    } catch (error) {
        console.error('Error fetching cognitive logs:', error);
        res.status(500).json({ error: 'Failed to fetch cognitive logs' });
    }
});

// Text-to-speech endpoint (proxy to Python media service)
router.post('/speak', async (req, res) => {
    try {
        const { text, lang = 'en' } = req.body;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        await CommandLog.create({
            command_type: 'speak',
            command_data: { text, lang },
            source: 'api'
        });

        // In production, this would call the Python media service
        // For now, just acknowledge
        res.json({ success: true, text, lang });
    } catch (error) {
        console.error('Error sending speak command:', error);
        res.status(500).json({ error: 'Failed to send speak command' });
    }
});

// Update RGB
router.post('/control/rgb', async (req, res) => {
    try {
        const { hue, sat, bri, swi } = req.body;

        const state = await RobotState.findOne().sort({ updated_at: -1 });
        if (state) {
            if (hue !== undefined) state.rgb.hue = hue;
            if (sat !== undefined) state.rgb.sat = sat;
            if (bri !== undefined) state.rgb.bri = bri;
            if (swi !== undefined) state.rgb.swi = swi;

            await state.save();
            req.app.get('io').emit('state', state);

            await CommandLog.create({
                command_type: 'rgb',
                command_data: { hue, sat, bri, swi },
                source: 'api'
            });
        }

        res.json({ success: true, rgb: state.rgb });
    } catch (error) {
        console.error('Error updating RGB:', error);
        res.status(500).json({ error: 'Failed to update RGB' });
    }
});

// Update arm positions
router.post('/control/arm', async (req, res) => {
    try {
        const { arm1, arm2 } = req.body;

        const state = await RobotState.findOne().sort({ updated_at: -1 });
        if (state) {
            if (arm1 !== undefined) state.arm1 = Math.max(0, Math.min(180, arm1));
            if (arm2 !== undefined) state.arm2 = Math.max(0, Math.min(180, arm2));

            await state.save();
            req.app.get('io').emit('state', state);

            await CommandLog.create({
                command_type: 'arm',
                command_data: { arm1, arm2 },
                source: 'api'
            });
        }

        res.json({ success: true, arm1: state.arm1, arm2: state.arm2 });
    } catch (error) {
        console.error('Error updating arm:', error);
        res.status(500).json({ error: 'Failed to update arm positions' });
    }
});

export default router;
