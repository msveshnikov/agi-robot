import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './ControlButton.css';

const ControlButton = ({ 
  icon: Icon, 
  label, 
  active = false, 
  onClick, 
  disabled = false,
  variant = 'default' // default, primary, danger
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const handleMouseDown = () => setIsPressed(true);
  const handleMouseUp = () => setIsPressed(false);

  return (
    <motion.button
      className={`control-button ${active ? 'active' : ''} ${variant} ${disabled ? 'disabled' : ''}`}
      onClick={onClick}
      disabled={disabled}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      whileHover={!disabled ? { scale: 1.05 } : {}}
      whileTap={!disabled ? { scale: 0.95 } : {}}
    >
      <div className="control-button-icon">
        <Icon size={24} />
      </div>
      <div className="control-button-label">{label}</div>
      {active && <div className="control-button-indicator" />}
    </motion.button>
  );
};

export default ControlButton;
