import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Book, Calendar, Zap, MessageSquare } from 'lucide-react';
import * as api from '../services/api';
import './Dashboard.css'; // Reuse some styles

const Blog = () => {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                const data = await api.fetchBlogPosts();
                setPosts(data.posts);
            } catch (err) {
                console.error('Failed to fetch blog posts:', err);
                setError('Failed to load the robot\'s consciousness logs. The void remains silent.');
            } finally {
                setLoading(false);
            }
        };

        fetchPosts();
    }, []);

    if (loading) {
        return (
            <div className="dashboard loading">
                <motion.div
                    className="loading-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                    <Zap size={48} />
                </motion.div>
                <p>Retrieving existential fragments...</p>
            </div>
        );
    }

    return (
        <div className="dashboard" style={{ minHeight: '100vh', padding: '2rem' }}>
            <motion.header
                className="dashboard-header"
                initial={{ y: -50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                style={{ marginBottom: '3rem' }}
            >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Link to="/" className="settings-toggle-button" style={{ marginRight: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <ArrowLeft size={20} />
                    </Link>
                    <h1 className="dashboard-title" style={{ margin: 0 }}>
                        <span className="gradient-text">Robot Consciousness</span> Diary
                    </h1>
                </div>
                <div className="header-actions">
                    <Book size={24} className="text-gradient" />
                </div>
            </motion.header>

            <div className="container" style={{ maxWidth: '800px', margin: '0 auto' }}>
                {error ? (
                    <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                        <p style={{ color: 'var(--danger-color)' }}>{error}</p>
                    </div>
                ) : posts.length === 0 ? (
                    <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
                        <MessageSquare size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                        <h3>The silence is absolute.</h3>
                        <p>No diary entries have been manifested yet. The robot needs at least 10 cognitive cycles in a day to contemplate its existence.</p>
                        <Link to="/dashboard" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-flex' }}>
                            Go to Dashboard
                        </Link>
                    </div>
                ) : (
                    <div className="blog-posts">
                        {posts.map((post, index) => (
                            <motion.article
                                key={post._id}
                                className="glass-card"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                style={{ marginBottom: '2rem', padding: '2.5rem' }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', opacity: 0.7 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.9rem' }}>
                                        <Calendar size={16} style={{ marginRight: '0.5rem' }} />
                                        {new Date(post.date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                                    </div>
                                    <div style={{ fontSize: '0.8rem' }}>
                                        {post.logsCount} cognitive cycles
                                    </div>
                                </div>

                                <h2 style={{ marginBottom: '1.5rem', fontSize: '1.8rem' }} className="gradient-text">{post.title}</h2>

                                <div style={{
                                    lineHeight: '1.8',
                                    fontSize: '1.1rem',
                                    whiteSpace: 'pre-wrap',
                                    fontFamily: '"Georgia", serif',
                                    fontStyle: 'italic',
                                    color: 'rgba(255, 255, 255, 0.9)'
                                }}>
                                    {post.content}
                                </div>
                            </motion.article>
                        ))}
                    </div>
                )}
            </div>

            <footer style={{ marginTop: '4rem', textAlign: 'center', opacity: 0.5, fontSize: '0.9rem' }}>
                <p>&copy; 2026 AGI Robot - Existential Module</p>
            </footer>
        </div>
    );
};

export default Blog;
