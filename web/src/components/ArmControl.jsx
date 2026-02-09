import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, RotateCcw } from 'lucide-react';
import './ArmControl.css';

const ArmControl = ({ arm1, arm2, onUpdate }) => {
    const [localArm1, setLocalArm1] = useState(arm1 || 0);
    const [localArm2, setLocalArm2] = useState(arm2 || 0);

    // Sync with prop updates
    useEffect(() => {
        if (arm1 !== undefined) setLocalArm1(arm1);
    }, [arm1]);

    useEffect(() => {
        if (arm2 !== undefined) setLocalArm2(arm2);
    }, [arm2]);

    const handleArm1Change = (e) => {
        const value = parseInt(e.target.value);
        setLocalArm1(value);
        onUpdate({ arm1: value, arm2: localArm2 });
    };

    const handleArm2Change = (e) => {
        const value = parseInt(e.target.value);
        setLocalArm2(value);
        onUpdate({ arm1: localArm1, arm2: value });
    };

    const resetArms = () => {
        setLocalArm1(0);
        setLocalArm2(0);
        onUpdate({ arm1: 0, arm2: 0 });
    };

    return (
        <div className="arm-control">
            <div className="arm-header">
                <div className="arm-title-group">
                    <Cpu className="arm-icon" size={24} />
                    <h3 className="arm-title">Manipulator Arms</h3>
                </div>
                <button
                    className="arm-reset-button"
                    onClick={resetArms}
                    title="Reset to 0°"
                >
                    <RotateCcw size={18} />
                </button>
            </div>

            <div className="arm-sliders">
                <div className="arm-slider-group">
                    <div className="slider-labels">
                        <label>Arm 1 (Base Rotation)</label>
                        <span className="angle-value">{localArm1}°</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="180"
                        value={localArm1}
                        onChange={handleArm1Change}
                        className="arm-slider"
                    />
                    <div className="slider-ticks">
                        <span>0°</span>
                        <span>90°</span>
                        <span>180°</span>
                    </div>
                </div>

                <div className="arm-slider-group">
                    <div className="slider-labels">
                        <label>Arm 2 (Tilt Rotation)</label>
                        <span className="angle-value">{localArm2}°</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="180"
                        value={localArm2}
                        onChange={handleArm2Change}
                        className="arm-slider"
                    />
                    <div className="slider-ticks">
                        <span>0°</span>
                        <span>90°</span>
                        <span>180°</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ArmControl;
