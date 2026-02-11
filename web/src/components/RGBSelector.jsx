import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Palette, Lightbulb, LightbulbOff } from 'lucide-react';
import './RGBSelector.css';

const RGBSelector = ({ rgb, onUpdate }) => {
    const [localColor, setLocalColor] = useState('#000000');
    const [brightness, setBrightness] = useState(rgb?.bri || 100);
    const [isOn, setIsOn] = useState(rgb?.swi !== false);

    // Sync with prop updates
    useEffect(() => {
        if (rgb) {
            const hex = hsvToHex(rgb.hue, rgb.sat, rgb.bri);
            setLocalColor(hex);
            setBrightness(rgb.bri);
            setIsOn(rgb.swi);
        }
    }, [rgb]);

    const hsvToHex = (h, s, v) => {
        s /= 100;
        v /= 100;
        let r, g, b;
        let i = Math.floor(h / 60);
        let f = h / 60 - i;
        let p = v * (1 - s);
        let q = v * (1 - f * s);
        let t = v * (1 - (1 - f) * s);

        switch (i % 6) {
            case 0: r = v; g = t; b = p; break;
            case 1: r = q; g = v; b = p; break;
            case 2: r = p; g = v; b = t; break;
            case 3: r = p; g = q; b = v; break;
            case 4: r = t; g = p; b = v; break;
            case 5: r = v; g = p; b = q; break;
            default: r = 0; g = 0; b = 0;
        }

        const toHex = (x) => Math.round(x * 255).toString(16).padStart(2, '0');
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    };

    const hexToHsv = (hex) => {
        let r = parseInt(hex.slice(1, 3), 16) / 255;
        let g = parseInt(hex.slice(3, 5), 16) / 255;
        let b = parseInt(hex.slice(5, 7), 16) / 255;

        let max = Math.max(r, g, b), min = Math.min(r, g, b);
        let h, s, v = max;

        let d = max - min;
        s = max === 0 ? 0 : d / max;

        if (max === min) {
            h = 0;
        } else {
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
                default: h = 0;
            }
            h /= 6;
        }

        return {
            hue: Math.round(h * 360),
            sat: Math.round(s * 100),
            bri: Math.round(v * 100)
        };
    };

    const handleColorChange = (e) => {
        const hex = e.target.value;
        setLocalColor(hex);
        const { hue, sat } = hexToHsv(hex);
        onUpdate({ hue, sat, bri: brightness, swi: isOn });
    };

    const handleBrightnessChange = (e) => {
        const bri = parseInt(e.target.value);
        setBrightness(bri);
        const { hue, sat } = hexToHsv(localColor);
        onUpdate({ hue, sat, bri, swi: isOn });
    };

    const toggleSwitch = () => {
        const newSwi = !isOn;
        setIsOn(newSwi);
        const { hue, sat } = hexToHsv(localColor);
        onUpdate({ hue, sat, bri: brightness, swi: newSwi });
    };

    return (
        <div className="rgb-selector">
            <div className="rgb-header">
                <div className="rgb-title-group">
                    <Palette className="rgb-icon" size={24} />
                    <h3 className="rgb-title">Status Light</h3>
                </div>
                <button
                    className={`rgb-power-button ${isOn ? 'on' : 'off'}`}
                    onClick={toggleSwitch}
                >
                    {isOn ? <Lightbulb size={20} /> : <LightbulbOff size={20} />}
                </button>
            </div>

            <div className="rgb-controls">
                <div className="color-picker-wrapper">
                    <input
                        type="color"
                        value={localColor}
                        onChange={handleColorChange}
                        className="color-input"
                        disabled={!isOn}
                    />
                    <div className="color-preview" style={{ backgroundColor: isOn ? localColor : '#333' }}>
                        <div className="color-glow" style={{ boxShadow: isOn ? `0 0 20px ${localColor}` : 'none' }} />
                    </div>
                </div>

                <div className="brightness-control">
                    <div className="slider-labels">
                        <span>Brightness</span>
                        <span>{brightness}%</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={brightness}
                        onChange={handleBrightnessChange}
                        className="brightness-slider"
                        disabled={!isOn}
                    />
                </div>
            </div>
        </div>
    );
};

export default RGBSelector;
