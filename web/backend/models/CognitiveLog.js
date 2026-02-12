import mongoose from "mongoose";

const cognitiveLogSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },
    plan: { type: String, default: "" },
    subplan: { type: String, default: "" },
    memory: { type: String, default: "" },
    goal: { type: String, default: "" },
});

// Add index for faster querying
cognitiveLogSchema.index({ timestamp: -1 });

const CognitiveLog = mongoose.model("CognitiveLog", cognitiveLogSchema);

export default CognitiveLog;
