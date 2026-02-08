import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { History, Brain, Target, Database, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import * as api from '../services/api';
import socketService from '../services/socket';
import './CognitiveHistory.css';

const CognitiveHistory = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState(null);

    const fetchLogs = async () => {
        try {
            const data = await api.fetchCognitiveLogs({ limit: 50 });
            setLogs(data.logs);
        } catch (error) {
            console.error('Failed to fetch cognitive logs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();

        // Listen for real-time cognitive updates
        socketService.on('cognitive', (newLog) => {
            setLogs(prevLogs => [newLog, ...prevLogs.slice(0, 10)]);
        });

        return () => {
            socketService.off('cognitive');
        };
    }, []);

    const toggleExpand = (id) => {
        setExpandedId(expandedId === id ? null : id);
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    if (loading) {
        return <div className="cognitive-history loading">Loading history...</div>;
    }

    return (
        <div className="cognitive-history glass-card">
            <div className="history-header">
                <History size={20} className="header-icon" />
                <h3 className="history-title">Cognitive State History</h3>
            </div>

            <div className="history-list">
                {logs.length === 0 ? (
                    <div className="no-logs">No cognitive history yet.</div>
                ) : (
                    logs.map((log, index) => (
                        <motion.div
                            key={log._id || index}
                            className={`history-item ${expandedId === (log._id || index) ? 'expanded' : ''}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <div className="item-summary" onClick={() => toggleExpand(log._id || index)}>
                                <div className="item-time">
                                    <Clock size={14} />
                                    <span>{formatDate(log.timestamp)}</span>
                                </div>
                                <div className="item-main-goal">
                                    <Target size={14} className="goal-icon" />
                                    <span className="truncate">{log.plan || 'No active plan'}</span>
                                </div>
                                {expandedId === (log._id || index) ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>

                            <AnimatePresence>
                                {expandedId === (log._id || index) && (
                                    <motion.div
                                        className="item-details"
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                    >
                                        <div className="detail-section">
                                            <div className="detail-label"><Target size={12} /> Goal</div>
                                            <div className="detail-value">{log.goal || 'No goal set'}</div>
                                        </div>
                                        <div className="detail-section">
                                            <div className="detail-label"><Brain size={12} /> Plan</div>
                                            <div className="detail-value">{log.plan || 'None'}</div>
                                        </div>
                                        {log.subplan && (
                                            <div className="detail-section">
                                                <div className="detail-label"><Clock size={12} /> Subplan</div>
                                                <div className="detail-value">{log.subplan}</div>
                                            </div>
                                        )}
                                        {log.memory && (
                                            <div className="detail-section">
                                                <div className="detail-label"><Database size={12} /> Memory</div>
                                                <div className="detail-value memory-box">{log.memory}</div>
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
};

export default CognitiveHistory;
