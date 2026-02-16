import mongoose from 'mongoose';

const telemetryLogSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now, index: true },
    distance: { type: Number, required: true },
    temperature: { type: Number },
    humidity: { type: Number }
});

// Create index for efficient time-based queries
telemetryLogSchema.index({ timestamp: -1 });

const TelemetryLog = mongoose.model('TelemetryLog', telemetryLogSchema);

export default TelemetryLog;
