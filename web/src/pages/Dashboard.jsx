import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Gauge, Thermometer, Droplets, Brain, AlertTriangle,
    ArrowUp, ArrowDown, ArrowLeft, ArrowRight, StopCircle,
    Power, Zap, Settings, MessageSquare
} from 'lucide-react';
import TelemetryCard from '../components/TelemetryCard';
import ControlButton from '../components/ControlButton';
import SettingsPanel from '../components/SettingsPanel';
import CameraFeed from '../components/CameraFeed';
import RGBSelector from '../components/RGBSelector';
import ArmControl from '../components/ArmControl';
import CognitiveHistory from '../components/CognitiveHistory';
import socketService from '../services/socket';
import * as api from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const [robotState, setRobotState] = useState(null);
    const [telemetry, setTelemetry] = useState({
        distance: 0,
        temperature: 0,
        humidity: 0
    });
    const [lastTelemetryTime, setLastTelemetryTime] = useState(null);
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [settingsOpen, setSettingsOpen] = useState(false);

    // Fetch initial state
    useEffect(() => {
        const fetchInitialState = async () => {
            try {
                const state = await api.fetchState();
                setRobotState(state);
                setTelemetry({
                    distance: state.distance || 0,
                    temperature: state.temperature || 0,
                    humidity: state.humidity || 0
                });
                if (state.updatedAt || state.updated_at) {
                    setLastTelemetryTime(new Date(state.updatedAt || state.updated_at).getTime());
                }
            } catch (error) {
                console.error('Failed to fetch initial state:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchInitialState();
    }, []);

    // Connect to Socket.IO
    useEffect(() => {
        socketService.connect();

        socketService.on('connect', () => {
            console.log('Socket connected');
        });

        socketService.on('disconnect', () => {
            console.log('Socket disconnected');
        });

        // Listen for state updates
        socketService.on('state', (state) => {
            setRobotState(state);
        });

        // Listen for telemetry updates
        socketService.on('telemetry', (data) => {
            setTelemetry({
                distance: data.distance,
                temperature: data.temperature,
                humidity: data.humidity
            });
            setLastTelemetryTime(Date.now());
        });

        return () => {
            socketService.off('state');
            socketService.off('telemetry');
        };
    }, []);

    // Connection monitor effect
    useEffect(() => {
        const checkConnection = () => {
            if (!lastTelemetryTime) {
                setConnected(false);
                return;
            }
            const now = Date.now();
            const isConnected = now - lastTelemetryTime < 10000;
            setConnected(isConnected);
        };

        // Check immediately
        checkConnection();

        const interval = setInterval(checkConnection, 1000);
        return () => clearInterval(interval);
    }, [lastTelemetryTime]);

    const handleMoveCommand = async (direction) => {
        try {
            await api.sendMoveCommand(direction, 100, 0, robotState?.speed || 45);
        } catch (error) {
            console.error('Move command failed:', error);
        }
    };

    const handleStop = async () => {
        try {
            await api.sendMoveCommand('stop', 0, 0, 0);
        } catch (error) {
            console.error('Stop command failed:', error);
        }
    };

    const toggleAGI = async () => {
        try {
            const newState = !robotState?.agi;
            await api.toggleAGI(newState);
        } catch (error) {
            console.error('AGI toggle failed:', error);
        }
    };

    const togglePanic = async () => {
        try {
            const newState = !robotState?.panic;
            await api.togglePanic(newState);
        } catch (error) {
            console.error('Panic toggle failed:', error);
        }
    };

    const handleRGBUpdate = async (rgbData) => {
        try {
            await api.updateRGB(rgbData.hue, rgbData.sat, rgbData.bri, rgbData.swi);
        } catch (error) {
            console.error('RGB update failed:', error);
        }
    };

    const handleArmUpdate = async (armData) => {
        try {
            await api.updateArm(armData.arm1, armData.arm2);
        } catch (error) {
            console.error('Arm update failed:', error);
        }
    };

    if (loading) {
        return (
            <div className="dashboard loading">
                <motion.div
                    className="loading-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                    <Zap size={48} />
                </motion.div>
                <p>Connecting to robot...</p>
            </div>
        );
    }

    return (
        <div className="dashboard">
            {/* Header */}
            <motion.header
                className="dashboard-header"
                initial={{ y: -50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
            >
                <h1 className="dashboard-title">
                    <span className="text-gradient">AGI Robot</span> Control Dashboard
                </h1>
                <div className="header-actions">
                    <div className="connection-status">
                        <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`} />
                        <span>{connected ? 'Robot Online' : 'Robot Offline'}</span>
                    </div>
                    <button
                        className="settings-toggle-button"
                        onClick={() => window.location.href = '/blog'}
                        title="Robot Diary"
                        style={{ marginRight: '10px' }}
                    >
                        <MessageSquare size={20} />
                    </button>
                    <button
                        className="settings-toggle-button"
                        onClick={() => setSettingsOpen(true)}
                        title="Open Settings"
                    >
                        <Settings size={20} />
                    </button>
                </div>
            </motion.header>

            {/* Main Content */}
            <div className="dashboard-content">
                {/* Telemetry Section */}
                <motion.section
                    className="dashboard-section telemetry-section"
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <h2 className="section-title">Live Telemetry</h2>
                    <div className="telemetry-grid">
                        <TelemetryCard
                            icon={Gauge}
                            label="Distance"
                            value={telemetry.distance}
                            unit="cm"
                            threshold={25}
                            warningBelow={true}
                        />
                        <TelemetryCard
                            icon={Thermometer}
                            label="Temperature"
                            value={telemetry.temperature}
                            unit="°C"
                        />
                        <TelemetryCard
                            icon={Droplets}
                            label="Humidity"
                            value={telemetry.humidity}
                            unit="%"
                        />
                    </div>
                </motion.section>

                {/* Camera Feed Section */}
                <motion.section
                    className="dashboard-section camera-section"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.15 }}
                >
                    <CameraFeed />
                </motion.section>

                {/* Movement Controls */}
                <motion.section
                    className="dashboard-section controls-section"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <h2 className="section-title">Movement Controls</h2>
                    <div className="movement-controls">
                        <div className="control-spacer"></div>
                        <ControlButton
                            icon={ArrowUp}
                            label="Forward"
                            active={robotState?.forward}
                            onClick={() => handleMoveCommand('forward')}
                        />
                        <div className="control-spacer"></div>

                        <ControlButton
                            icon={ArrowLeft}
                            label="Left"
                            active={robotState?.left}
                            onClick={() => handleMoveCommand('left')}
                        />
                        <ControlButton
                            icon={StopCircle}
                            label="Stop"
                            onClick={handleStop}
                            variant="danger"
                        />
                        <ControlButton
                            icon={ArrowRight}
                            label="Right"
                            active={robotState?.right}
                            onClick={() => handleMoveCommand('right')}
                        />

                        <div className="control-spacer"></div>
                        <ControlButton
                            icon={ArrowDown}
                            label="Back"
                            active={robotState?.back}
                            onClick={() => handleMoveCommand('back')}
                        />
                        <div className="control-spacer"></div>
                    </div>
                </motion.section>

                {/* Mode Controls */}
                <motion.section
                    className="dashboard-section mode-section"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <h2 className="section-title">Robot Modes</h2>
                    <div className="mode-controls">
                        <ControlButton
                            icon={Brain}
                            label="AGI Mode"
                            active={robotState?.agi}
                            onClick={toggleAGI}
                            variant="primary"
                        />
                        <ControlButton
                            icon={AlertTriangle}
                            label="Panic Mode"
                            active={robotState?.panic}
                            onClick={togglePanic}
                            variant="danger"
                        />
                        <ControlButton
                            icon={Power}
                            label={`ASI ${robotState?.asi ? 'ON' : 'OFF'}`}
                            active={robotState?.asi}
                            variant={robotState?.asi ? 'primary' : 'default'}
                        />
                    </div>
                </motion.section>

                {/* RGB Control Section */}
                <motion.section
                    className="dashboard-section rgb-section"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.35 }}
                >
                    <h2 className="section-title">RGB Control</h2>
                    <RGBSelector
                        rgb={robotState?.rgb}
                        onUpdate={handleRGBUpdate}
                    />
                </motion.section>

                {/* Speed Display */}
                <motion.section
                    className="dashboard-section speed-section"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                >
                    <h2 className="section-title">Current Speed</h2>
                    <div className="speed-display glass-card">
                        <div className="speed-value">
                            {robotState?.speed || 45}
                            <span className="speed-unit">RPM</span>
                        </div>
                        <div className="speed-bar">
                            <motion.div
                                className="speed-bar-fill"
                                initial={{ width: 0 }}
                                animate={{ width: `${((robotState?.speed || 45) / 90) * 100}%` }}
                                transition={{ duration: 0.5 }}
                            />
                        </div>
                    </div>
                </motion.section>

                {/* Arm Control Section */}
                <motion.section
                    className="dashboard-section arm-section"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.42 }}
                >
                    <ArmControl
                        arm1={robotState?.arm1}
                        arm2={robotState?.arm2}
                        onUpdate={handleArmUpdate}
                    />
                </motion.section>

                {/* Cognitive History Section */}
                <motion.section
                    className="dashboard-section history-section"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.45 }}
                >
                    <CognitiveHistory />
                </motion.section>
            </div>

            {/* Settings Panel */}
            <SettingsPanel
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                currentState={robotState}
            />
        </div>
    );
};

export default Dashboard;
