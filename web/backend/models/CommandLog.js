import mongoose from "mongoose";

const commandLogSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now, index: true },
    command_type: {
        type: String,
        required: true,
        enum: ["move", "turn", "stop", "agi", "panic", "speak", "rgb", "arm"],
    },
    command_data: { type: mongoose.Schema.Types.Mixed },
    llm_response: { type: mongoose.Schema.Types.Mixed },
    source: {
        type: String,
        enum: ["user", "agi", "panic", "api"],
        default: "user",
    },
});

// Create index for efficient time-based queries and filtering
commandLogSchema.index({ timestamp: -1, command_type: 1 });

const CommandLog = mongoose.model("CommandLog", commandLogSchema);

export default CommandLog;
