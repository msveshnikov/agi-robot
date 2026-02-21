import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calendar, Zap, MessageSquare } from 'lucide-react';
import * as api from '../services/api';
import './Dashboard.css';
import './Blog.css';

const BlogPostImage = ({ date }) => {
    const [hasError, setHasError] = useState(false);

    // Format: YYYYMMDD
    const formatDateToYYYYMMDD = (dateString) => {
        try {
            const date = new Date(dateString);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}${month}${day}`;
        } catch {
            return null;
        }
    };

    const imageName = formatDateToYYYYMMDD(date);
    if (hasError || !imageName) return null;

    return (
        <motion.div
            className="blog-post-image"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
        >
            <img
                src={`/${imageName}.jpg`}
                alt={`Experience captured on ${imageName}`}
                onError={() => setHasError(true)}
            />
        </motion.div>
    );
};

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
        <div className="dashboard blog-dashboard">
            <motion.header
                className="dashboard-header blog-header"
                initial={{ y: -50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
            >
                <div className="blog-header-content">
                    <Link to="/" className="settings-toggle-button blog-back-button">
                        <ArrowLeft size={20} />
                    </Link>
                    <h1 className="dashboard-title blog-title-text">
                        <span className="gradient-text">Robot</span> Diary
                    </h1>
                </div>
            </motion.header>

            <div className="container blog-container">
                {error ? (
                    <div className="glass-card blog-empty-state">
                        <p style={{ color: 'var(--danger-color)' }}>{error}</p>
                    </div>
                ) : posts.length === 0 ? (
                    <div className="glass-card blog-empty-state">
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
                                className="glass-card blog-post"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <BlogPostImage date={post.date} />
                                <div className="blog-post-meta">
                                    <div className="blog-post-date">
                                        <Calendar size={16} style={{ marginRight: '0.5rem' }} />
                                        {new Date(post.date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                                    </div>
                                    <div className="blog-post-cycles">
                                        {post.logsCount} cognitive cycles
                                    </div>
                                </div>

                                <h2 className="blog-post-title gradient-text">{post.title}</h2>

                                <div className="blog-post-text">
                                    {post.content}
                                </div>
                            </motion.article>
                        ))}
                    </div>
                )}
            </div>

            <footer className="blog-footer">
                <p>&copy; 2026 MaxSoft - Existential Module</p>
            </footer>
        </div>
    );
};

export default Blog;
