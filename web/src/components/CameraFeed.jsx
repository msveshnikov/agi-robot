import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, CameraOff, Circle } from 'lucide-react';
import socketService from '../services/socket';
import './CameraFeed.css';

const CameraFeed = () => {
    const [frame, setFrame] = useState(null);
    const [lastFrameTime, setLastFrameTime] = useState(0);
    const [active, setActive] = useState(false);

    useEffect(() => {
        const handleCameraFrame = (data) => {
            // data can be base64 string or binary
            let frameSource = data;
            if (typeof data === 'string' && !data.startsWith('data:image')) {
                frameSource = `data:image/jpeg;base64,${data}`;
            } else if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
                // Handle binary if needed
                const blob = new Blob([data], { type: 'image/jpeg' });
                frameSource = URL.createObjectURL(blob);
            } else if (typeof data === 'object' && data !== null) {
                // Handle object wrapper (e.g. { image: 'b64...' })
                const possibleKeys = ['b64', 'image', 'img', 'data', 'payload', 'base64'];
                let foundData = null;
                for (const key of possibleKeys) {
                    if (data[key] && typeof data[key] === 'string') {
                        foundData = data[key];
                        break;
                    }
                }

                if (foundData) {
                    if (!foundData.startsWith('data:image')) {
                        frameSource = `data:image/jpeg;base64,${foundData}`;
                    } else {
                        frameSource = foundData;
                    }
                }
            }

            setFrame(frameSource);
            setLastFrameTime(Date.now());
            setActive(true);
        };

        const handleSpeech = (data) => {
            if (data && data.audio) {
                console.log("Receiving robot speech broadcast:", data.text);
                const audioUrl = `data:audio/wav;base64,${data.audio}`;
                const audio = new Audio(audioUrl);
                audio.play().catch(e => console.error("Error playing broadcasted speech:", e));
            }
        };

        socketService.on('camera', handleCameraFrame);
        socketService.on('speech', handleSpeech);

        // Heartbeat to detect stale feed
        const interval = setInterval(() => {
            if (Date.now() - lastFrameTime > 2000) {
                setActive(false);
            }
        }, 1000);

        return () => {
            socketService.off('camera', handleCameraFrame);
            socketService.off('speech', handleSpeech);
            clearInterval(interval);
        };
    }, [lastFrameTime]);

    return (
        <div className="camera-feed-container glass-card">
            <div className="camera-header">
                <div className="camera-title-group">
                    <Camera size={18} className="camera-icon" />
                    <h3 className="camera-title">Live Camera Feed</h3>
                </div>
                {active && (
                    <div className="live-indicator">
                        <Circle size={8} fill="currentColor" className="live-dot" />
                        <span>LIVE</span>
                    </div>
                )}
            </div>

            <div className="camera-display">
                <AnimatePresence mode="wait">
                    {active && frame ? (
                        <motion.img
                            key="feed"
                            src={frame}
                            alt="Robot Feed"
                            className="feed-image"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                        />
                    ) : (
                        <motion.div
                            key="placeholder"
                            className="feed-placeholder"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <CameraOff size={48} className="placeholder-icon" />
                            <p>No active camera feed</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="camera-footer">
                <span className="camera-meta">
                    {active ? 'Streaming @ ~10 FPS' : 'Idle'}
                </span>
            </div>
        </div>
    );
};

export default CameraFeed;
