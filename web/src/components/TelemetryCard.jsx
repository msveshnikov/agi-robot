import React from "react";
import { motion } from "framer-motion";
import "./TelemetryCard.css";

// eslint-disable-next-line no-unused-vars
const TelemetryCard = ({ icon: Icon, label, value, unit, threshold, warningBelow }) => {
    // Determine if value is in warning range
    const isWarning = threshold && (warningBelow ? value < threshold : value > threshold);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`telemetry-card glass-card ${isWarning ? "warning" : ""}`}
        >
            <div className="telemetry-icon">
                <Icon size={32} />
            </div>
            <div className="telemetry-content">
                <div className="telemetry-label">{label}</div>
                <div className="telemetry-value">
                    {typeof value === "number" ? value.toFixed(1) : value}
                    {unit && <span className="telemetry-unit">{unit}</span>}
                </div>
            </div>
        </motion.div>
    );
};

export default TelemetryCard;
