import mongoose from "mongoose";

const robotStateSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },

    // Control Variables
    agi: { type: Boolean, default: false },
    asi: { type: Boolean, default: false },
    speed: { type: Number, default: 45, min: 0, max: 90 },
    panic: { type: Boolean, default: false },
    forward: { type: Boolean, default: false },
    back: { type: Boolean, default: false },
    left: { type: Boolean, default: false },
    right: { type: Boolean, default: false },
    lang: { type: String, default: "en" },
    goal: { type: String, default: "Be helpful assistant to the master human" },

    // RGB Control (HSV format from Backend)
    rgb: {
        hue: { type: Number, default: 0, min: 0, max: 360 },
        sat: { type: Number, default: 0, min: 0, max: 100 },
        bri: { type: Number, default: 100, min: 0, max: 100 },
        swi: { type: Boolean, default: true },
    },

    // Arm Control
    arm1: { type: Number, default: 0, min: 0, max: 180 },
    arm2: { type: Number, default: 0, min: 0, max: 180 },

    // Audio Control
    volume: { type: Number, default: 70, min: 0, max: 100 },

    // Telemetry (Read-only from robot)
    distance: { type: Number, default: 0 },
    temperature: { type: Number, default: 0 },
    humidity: { type: Number, default: 0 },

    // Planning & Memory
    plan: { type: String, default: "" },
    subplan: { type: String, default: "" },
    space_map: { type: String, default: "" },
    movement_history: { type: [String], default: [] },
    memory: { type: String, default: "" },

    // Alarm
    alarm: { type: String, default: "" },
});

// Update timestamp on save
robotStateSchema.pre("save", function (next) {
    this.timestamp = Date.now();
    next();
});

const RobotState = mongoose.model("RobotState", robotStateSchema);

export default RobotState;
