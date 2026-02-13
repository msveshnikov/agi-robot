import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Settings as SettingsIcon,
    Globe,
    Zap,
    Target,
    Save,
    X,
    ChevronRight,
    MessageSquare,
    Shield,
    Activity,
    Map,
    Volume2,
} from "lucide-react";
import * as api from "../services/api";
import "./SettingsPanel.css";

const SettingsPanel = ({ isOpen, onClose, currentState }) => {
    const [language, setLanguage] = useState(() => currentState?.lang || "en");
    const [speed, setSpeed] = useState(() => currentState?.speed || 45);
    const [volume, setVolume] = useState(() => currentState?.volume || 70);
    const [goal, setGoal] = useState(() => currentState?.goal || "Be helpful assistant to the master human");
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.updateState({
                lang: language,
                speed: parseInt(speed),
                volume: parseInt(volume),
                goal: goal,
            });

            // Close panel after successful save
            setTimeout(() => {
                setSaving(false);
                onClose();
            }, 500);
        } catch (error) {
            console.error("Failed to save settings:", error);
            setSaving(false);
        }
    };

    const languages = [
        { code: "en", name: "English", flag: "🇬🇧" },
        { code: "de", name: "Deutsch", flag: "🇩🇪" },
        { code: "it", name: "Italiano", flag: "🇮🇹" },
        { code: "ru", name: "Русский", flag: "🇷🇺" },
        { code: "cs", name: "Čeština", flag: "🇨🇿" },
        { code: "disabled", name: "Voice Disabled", flag: "🔇" },
    ];

    const presets = [
        {
            id: "assistant",
            icon: <MessageSquare size={18} />,
            label: "Assistant",
            text: "Be helpful assistant to the master human",
        },
        {
            id: "explorer",
            icon: <Map size={18} />,
            label: "Explorer",
            text: "Explore the environment and map the space",
        },
        {
            id: "guard",
            icon: <Shield size={18} />,
            label: "Guard",
            text: "Guard the perimeter and detect intruders",
        },
        {
            id: "personal",
            icon: <Activity size={18} />,
            label: "Personal",
            text: "Follow the human and assist with tasks",
        },
    ];

    // Animation variants
    const panelVariants = {
        hidden: { x: "100%" },
        visible: {
            x: 0,
            transition: {
                type: "spring",
                damping: 30,
                stiffness: 300,
                staggerChildren: 0.1,
                delayChildren: 0.2,
            },
        },
        exit: {
            x: "100%",
            transition: { type: "spring", damping: 30, stiffness: 300 },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { type: "spring", damping: 20, stiffness: 200 },
        },
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    className="settings-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                >
                    <motion.div
                        className="settings-panel glass-card"
                        variants={panelVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="settings-header">
                            <h2 className="settings-title">
                                <span className="icon-wrapper">
                                    <SettingsIcon size={24} />
                                </span>
                                Settings
                            </h2>
                            <button className="close-button" onClick={onClose}>
                                <X size={24} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="settings-content">
                            {/* Language Setting */}
                            <motion.div className="setting-group" variants={itemVariants}>
                                <div className="group-header">
                                    <Globe size={20} className="group-icon" />
                                    <span className="group-title">Voice Interface</span>
                                </div>
                                <div className="select-wrapper">
                                    <select
                                        className="setting-select"
                                        value={language}
                                        onChange={(e) => setLanguage(e.target.value)}
                                    >
                                        {languages.map((lang) => (
                                            <option key={lang.code} value={lang.code}>
                                                {lang.flag} {lang.name}
                                            </option>
                                        ))}
                                    </select>
                                    <ChevronRight className="select-arrow" size={16} />
                                </div>
                                <p className="setting-description">
                                    Primary language for voice synthesis and interaction.
                                </p>
                            </motion.div>

                            {/* Speed Setting */}
                            <motion.div className="setting-group" variants={itemVariants}>
                                <div className="group-header">
                                    <Zap size={20} className="group-icon" />
                                    <span className="group-title">Motor Speed</span>
                                    <span className="speed-badge">{speed}%</span>
                                </div>
                                <div className="speed-control-container">
                                    <div className="range-wrapper">
                                        <input
                                            type="range"
                                            min="0"
                                            max="90"
                                            value={speed}
                                            onChange={(e) => setSpeed(e.target.value)}
                                            className="speed-slider"
                                            style={{
                                                background: `linear-gradient(to right, var(--color-primary) ${(speed / 90) * 100}%, var(--color-bg-secondary) ${(speed / 90) * 100}%)`,
                                            }}
                                        />
                                    </div>
                                    <div className="speed-labels">
                                        <span>Idle</span>
                                        <span>Max</span>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Volume Setting */}
                            <motion.div className="setting-group" variants={itemVariants}>
                                <div className="group-header">
                                    <Volume2 size={20} className="group-icon" />
                                    <span className="group-title">Speaker Volume</span>
                                    <span className="speed-badge">{volume}%</span>
                                </div>
                                <div className="speed-control-container">
                                    <div className="range-wrapper">
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={volume}
                                            onChange={(e) => setVolume(e.target.value)}
                                            className="speed-slider"
                                            style={{
                                                background: `linear-gradient(to right, var(--color-primary) ${volume}%, var(--color-bg-secondary) ${volume}%)`,
                                            }}
                                        />
                                    </div>
                                    <div className="speed-labels">
                                        <span>Mute</span>
                                        <span>Max</span>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Goal Setting */}
                            <motion.div className="setting-group" variants={itemVariants}>
                                <div className="group-header">
                                    <Target size={20} className="group-icon" />
                                    <span className="group-title">Primary Directive</span>
                                </div>

                                <div className="preset-grid">
                                    {presets.map((preset) => (
                                        <button
                                            key={preset.id}
                                            className={`preset-card ${goal === preset.text ? "active" : ""}`}
                                            onClick={() => setGoal(preset.text)}
                                        >
                                            <div className="preset-icon">{preset.icon}</div>
                                            <span className="preset-label">{preset.label}</span>
                                        </button>
                                    ))}
                                </div>

                                <textarea
                                    className="setting-textarea"
                                    value={goal}
                                    onChange={(e) => setGoal(e.target.value)}
                                    rows={4}
                                    placeholder="Define custom directive..."
                                />
                            </motion.div>
                        </div>

                        {/* Footer */}
                        <div className="settings-footer">
                            <button className="cancel-button" onClick={onClose} disabled={saving}>
                                Cancel
                            </button>
                            <button className="save-button" onClick={handleSave} disabled={saving}>
                                <Save size={18} />
                                {saving ? "Saving..." : "Save"}
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default SettingsPanel;
