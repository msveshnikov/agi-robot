import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';
import { ChevronLeft, FileText, Download, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import './AssemblyGuide.css';

const AssemblyGuide = () => {
    const [markdown, setMarkdown] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // In a real app, this would be fetched from an API or public folder
        // For now, we'll try to fetch the file content. 
        // Since it's outside the web root, we might need to move it or have a backend endpoint.
        // Assuming we'll expose a GET /docs/assembly-guide endpoint or similar.
        // For the sake of this task, I'll assume the markdown is served at /assembly_guide.md

        const fetchGuide = async () => {
            try {
                const response = await fetch('/api/docs/assembly-guide');
                if (response.ok) {
                    const data = await response.json();
                    setMarkdown(data.content);
                } else {
                    setMarkdown('# Error\nCould not load assembly guide. Please try again later.');
                }
            } catch (error) {
                console.error('Error fetching guide:', error);
                setMarkdown('# Error\nCould not load assembly guide. Please try again later.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchGuide();
    }, []);

    return (
        <div className="assembly-guide-page">
            <div className="guide-background"></div>

            <nav className="guide-nav">
                <div className="container">
                    <Link to="/" className="back-link">
                        <ChevronLeft size={20} />
                        <span>Back to Home</span>
                    </Link>
                </div>
            </nav>

            <main className="container guide-main">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="glass-card guide-card"
                >
                    {isLoading ? (
                        <div className="loading-state">
                            <div className="loader"></div>
                            <p>Loading Assembly Guide...</p>
                        </div>
                    ) : (
                        <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {markdown}
                            </ReactMarkdown>
                        </div>
                    )}
                </motion.div>
            </main>

            <footer className="guide-footer">
                <div className="container">
                    <p>&copy; 2026 MaxSoft. Documentation for AGI Robot.</p>
                </div>
            </footer>
        </div>
    );
};

export default AssemblyGuide;
