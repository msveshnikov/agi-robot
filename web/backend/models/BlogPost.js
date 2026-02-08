import mongoose from 'mongoose';

const blogPostSchema = new mongoose.Schema({
    title: { type: String, required: true },
    content: { type: String, required: true },
    date: { type: Date, default: Date.now },
    logsCount: { type: Number, required: true }
}, {
    timestamps: true
});

// Add index for date
blogPostSchema.index({ date: -1 });

const BlogPost = mongoose.model('BlogPost', blogPostSchema);

export default BlogPost;
