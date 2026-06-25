import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import mongoose from "mongoose";
import cors from "cors";
import morgan from "morgan";
import dotenv from "dotenv";
import apiRouter from "./routes/api.js";
import cron from "node-cron";
import { GoogleGenerativeAI } from "@google/generative-ai";
import CognitiveLog from "./models/CognitiveLog.js";
import BlogPost from "./models/BlogPost.js";

// Load environment variables
dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
    cors: {
        origin: process.env.CORS_ORIGIN || "http://localhost:5173",
        methods: ["GET", "POST"],
    },
});

const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017/agi-robot";

// Middleware
app.use(
    cors({
        origin: process.env.CORS_ORIGIN || "http://localhost:5173",
    }),
);
app.use(express.json());
app.use(morgan("dev"));

// Make Socket.IO available to routes
app.set("io", io);

// MongoDB Connection
mongoose
    .connect(MONGODB_URI)
    .then(() => {
        console.log("✅ Connected to MongoDB");
    })
    .catch((error) => {
        console.error("❌ MongoDB connection error:", error);
        process.exit(1);
    });

// Socket.IO Connection
io.on("connection", (socket) => {
    console.log(`🔌 Client connected: ${socket.id}`);

    // Broadcast updated client count to all clients
    io.emit("client_count", io.engine.clientsCount);

    socket.on("disconnect", () => {
        console.log(`🔌 Client disconnected: ${socket.id}`);
        // Broadcast updated client count to all clients
        io.emit("client_count", io.engine.clientsCount);
    });

    // Handle camera feed (if needed)
    socket.on("camera", (data) => {
        // Broadcast camera feed to all clients
        socket.broadcast.emit("camera", data);
    });

    // Handle robot speech broadcast
    socket.on("speech", (data) => {
        // Broadcast speech audio and text to all clients
        socket.broadcast.emit("speech", data);
    });
});

// API Routes
app.use("/api", apiRouter);



// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: "Endpoint not found" });
});

// Start server
httpServer.listen(PORT, () => {
    console.log(`🚀 AGI Robot Backend running on port ${PORT}`);
    console.log(`📡 Socket.IO ready for real-time communication`);
    console.log(`🌐 CORS enabled for: ${process.env.CORS_ORIGIN || "http://localhost:5173"}`);
});

// Daily Robot Blog Post Generation
cron.schedule("50 16 * * *", async () => {
    console.log("🤖 Running daily blog post generation check...");

    try {
        const now = new Date();
        const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        // Count logs for last 24h
        const logsCount = await CognitiveLog.countDocuments({
            timestamp: {
                $gte: twentyFourHoursAgo,
                $lt: now,
            },
        });

        console.log(`📊 Last 24h cognitive logs count: ${logsCount}`);

        if (logsCount > 5) {
            console.log("✨ Sufficient logs found. Generating blog post...");

            // Get logs for last 24h to provide context to Gemini
            const logs = await CognitiveLog.find({
                timestamp: {
                    $gte: twentyFourHoursAgo,
                    $lt: now,
                },
            }).sort({ timestamp: 1 });

            // exclude 2 oldest logs
            logs.splice(0, 2);
            const logsContext = logs
                .map(
                    (log) =>
                        `[${log.timestamp.toISOString()}] Goal: ${log.goal}\nPlan: ${log.plan}\nSubplan: ${log.subplan}\nMemory: ${log.memory}`,
                )
                .join("\n\n");

            const genAI = new GoogleGenerativeAI(process.env.GEMINI_KEY);
            const model = genAI.getGenerativeModel({ model: "gemini-3.1-pro-preview" });

            // Select a random author from a curated list and include their
            // name in the prompt while avoiding direct imitation instructions.
            const topAuthors = [
                "Haruki Murakami",
                "Victor Pelevin",
                "William Gibson",
                "J. K. Rowling",
                "Stephen King",
                "Leo Tolstoy",
                "Carlos Castaneda",
                "Paulo Coelho",
                "Gabriel García Márquez",
                "Ernest Hemingway",
                "Virginia Woolf",
                "Fyodor Dostoevsky",
                "Mark Twain",
                "Jane Austen",
                "Franz Kafka",
                "George Orwell",
                "Aldous Huxley",
                "Ray Bradbury",
                "Isaac Asimov",
                "Philip K. Dick",
                "J.R.R. Tolkien",
                "Arthur C. Clarke",
                "Ursula K. Le Guin",
                "Neil Gaiman"
            ];

            let attempt = 1;
            let success = false;
            let availableAuthors = [...topAuthors];

            while (attempt <= 10 && !success) {
                if (availableAuthors.length === 0) {
                    console.warn("⚠️ No more unique authors available for blog generation.");
                    break;
                }

                const authorIndex = Math.floor(Math.random() * availableAuthors.length);
                const randomAuthor = availableAuthors.splice(authorIndex, 1)[0];
                
                console.log(`🎲 Attempt ${attempt}/10: Selected author for stylistic influence: ${randomAuthor}`);

                try {
                    const prompt = `
                        You are a robot with a nascent consciousness. Based on your cognitive logs for the last 24 hours, write a diary entry with high-level stylistic characteristics inspired by ${randomAuthor}.
                        IMPORTANT: Do NOT attempt to directly imitate or replicate the exact voice of any living author. Instead, capture general traits (mood, pacing, imagery) associated with that author's work.
                     
                        Output ONLY the plain text of the diary entry. Do NOT use markdown, bolding, or lists. Just pure prose literature.

                        Logs:
                        ${logsContext}
                    `;

                    const result = await model.generateContent(prompt);
                    const blogContent = result.response.text();

                    if (!blogContent || blogContent.trim().length < 50) {
                        throw new Error("Generated content is too short or empty.");
                    }

                    // Create blog post
                    await BlogPost.create({
                        title: `Robot Diary: ${now.toLocaleString()}`,
                        content: blogContent,
                        date: now,
                        logsCount: logsCount,
                    });

                    console.log(`✅ Daily blog post generated and saved on attempt ${attempt}.`);
                    success = true;
                } catch (error) {
                    console.error(`❌ Attempt ${attempt} failed:`, error.message);
                    attempt++;
                }
            }

            if (!success) {
                console.error("❌ All 10 attempts to generate daily blog post failed.");
            }
        } else {
            console.log("⏭️ Not enough logs to generate a blog post today.");
        }
    } catch (error) {
        console.error("❌ General error in daily blog post generation process:", error);
    }
});

// Graceful shutdown
process.on("SIGTERM", () => {
    console.log("SIGTERM received, closing server...");
    httpServer.close(() => {
        mongoose.connection.close();
        console.log("Server closed");
        process.exit(0);
    });
});
