import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Globe, Zap, Target, Save, X } from 'lucide-react';
import * as api from '../services/api';
import './SettingsPanel.css';

const SettingsPanel = ({ isOpen, onClose, currentState }) => {
    const [language, setLanguage] = useState('en');
    const [speed, setSpeed] = useState(45);
    const [goal, setGoal] = useState('Be helpful assistant to the master human');
    const [saving, setSaving] = useState(false);

    // Initialize from current state
    useEffect(() => {
        if (currentState) {
            setLanguage(currentState.lang || 'en');
            setSpeed(currentState.speed || 45);
            setGoal(currentState.goal || 'Be helpful assistant to the master human');
        }
    }, [currentState]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.updateState({
                lang: language,
                speed: parseInt(speed),
                goal: goal
            });

            // Close panel after successful save
            setTimeout(() => {
                setSaving(false);
                onClose();
            }, 500);
        } catch (error) {
            console.error('Failed to save settings:', error);
            setSaving(false);
        }
    };

    const languages = [
        { code: 'en', name: 'English' },
        { code: 'de', name: 'Deutsch' },
        { code: 'it', name: 'Italiano' },
        { code: 'ru', name: 'Русский' },
        { code: 'cs', name: 'Čeština' },
        { code: 'disabled', name: 'Disabled' }
    ];

    if (!isOpen) return null;

    return (
        <motion.div
            className="settings-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="settings-panel glass-card"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25 }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="settings-header">
                    <h2 className="settings-title">
                        <SettingsIcon size={24} />
                        Robot Settings
                    </h2>
                    <button className="close-button" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="settings-content">
                    {/* Language Setting */}
                    <div className="setting-group">
                        <label className="setting-label">
                            <Globe size={20} />
                            <span>Voice Language</span>
                        </label>
                        <select
                            className="setting-select"
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                        >
                            {languages.map((lang) => (
                                <option key={lang.code} value={lang.code}>
                                    {lang.name}
                                </option>
                            ))}
                        </select>
                        <p className="setting-description">
                            Language for voice interactions and text-to-speech. Set to "Disabled" to turn off voice features.
                        </p>
                    </div>

                    {/* Speed Setting */}
                    <div className="setting-group">
                        <label className="setting-label">
                            <Zap size={20} />
                            <span>Motor Speed</span>
                        </label>
                        <div className="speed-control">
                            <input
                                type="range"
                                min="0"
                                max="90"
                                value={speed}
                                onChange={(e) => setSpeed(e.target.value)}
                                className="speed-slider"
                            />
                            <div className="speed-value-display">
                                {speed} <span className="unit">RPM</span>
                            </div>
                        </div>
                        <div className="speed-labels">
                            <span>Stop</span>
                            <span>Slow</span>
                            <span>Medium</span>
                            <span>Fast</span>
                            <span>Max</span>
                        </div>
                        <p className="setting-description">
                            Maximum motor speed for movement commands (0-90 RPM).
                        </p>
                    </div>

                    {/* Goal Setting */}
                    <div className="setting-group">
                        <label className="setting-label">
                            <Target size={20} />
                            <span>Robot Goal</span>
                        </label>
                        <textarea
                            className="setting-textarea"
                            value={goal}
                            onChange={(e) => setGoal(e.target.value)}
                            rows={4}
                            placeholder="Define the robot's primary objective..."
                        />
                        <p className="setting-description">
                            Primary objective that guides the robot's autonomous behavior and decision-making.
                        </p>
                    </div>

                    {/* Preset Goals */}
                    <div className="preset-goals">
                        <p className="preset-label">Quick Presets:</p>
                        <div className="preset-buttons">
                            <button
                                className="preset-button"
                                onClick={() => setGoal('Be helpful assistant to the master human')}
                            >
                                Default Assistant
                            </button>
                            <button
                                className="preset-button"
                                onClick={() => setGoal('Explore the environment and map the space')}
                            >
                                Explorer Mode
                            </button>
                            <button
                                className="preset-button"
                                onClick={() => setGoal('Guard the perimeter and detect intruders')}
                            >
                                Security Guard
                            </button>
                            <button
                                className="preset-button"
                                onClick={() => setGoal('Follow the human and assist with tasks')}
                            >
                                Personal Assistant
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="settings-footer">
                    <button className="cancel-button" onClick={onClose} disabled={saving}>
                        Cancel
                    </button>
                    <button
                        className="save-button"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        <Save size={18} />
                        {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default SettingsPanel;
