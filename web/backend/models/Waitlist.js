import mongoose from 'mongoose';

const waitlistSchema = new mongoose.Schema({
    email: {
        type: String,
        required: true,
        trim: true,
        lowercase: true
    },
    plan: {
        type: String,
        required: true,
        enum: ['Free', '$200', '$300']
    },
    timestamp: {
        type: Date,
        default: Date.now
    }
});

const Waitlist = mongoose.model('Waitlist', waitlistSchema);

export default Waitlist;
