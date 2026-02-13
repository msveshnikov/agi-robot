import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import {
    Brain,
    Shield,
    Map,
    Lightbulb,
    Github,
    ArrowRight,
    Zap,
    Eye,
    MessageSquare,
    Check
} from 'lucide-react';
import './LandingPage.css';
import './LandingPage-buttons.css';

const LandingPage = () => {
    const heroImages = [
        '/image-1.jpg',
        '/image-3.jpg',
        '/image-5.jpg'
    ];

    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [waitlistEmail, setWaitlistEmail] = useState('');
    const [selectedPlan, setSelectedPlan] = useState('Free');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null); // 'success' | 'error' | null

    const handleJoinWaitlist = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitStatus(null);

        try {
            const response = await fetch('/api/waitlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: waitlistEmail, plan: selectedPlan })
            });

            if (response.ok) {
                setSubmitStatus('success');
                setWaitlistEmail('');
            } else {
                setSubmitStatus('error');
            }
        } catch (error) {
            console.error('Waitlist error:', error);
            setSubmitStatus('error');
        } finally {
            setIsSubmitting(false);
        }
    };

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentImageIndex((prevIndex) =>
                (prevIndex + 1) % heroImages.length
            );
        }, 3000); // Change image every 3 seconds

        return () => clearInterval(interval);
    }, [heroImages.length]);

    const features = [
        {
            icon: <Brain size={32} />,
            title: 'Autonomous Navigation',
            description: 'LLM-driven pathfinding with obstacle avoidance and spatial mapping'
        },
        {
            icon: <Eye size={32} />,
            title: 'Computer Vision',
            description: 'Real-time image analysis for object detection and scene understanding'
        },
        {
            icon: <MessageSquare size={32} />,
            title: 'Voice Interaction',
            description: 'Dynamic audio recording (3-15s) with multi-language TTS support'
        },
        {
            icon: <Lightbulb size={32} />,
            title: 'Emotional Expression',
            description: 'RGB LED "mood" changes based on robot\'s state and decisions'
        },
        {
            icon: <Map size={32} />,
            title: 'Memory & Planning',
            description: 'Spatial maps, movement history, and hierarchical planning with persistence'
        },
        {
            icon: <Shield size={32} />,
            title: 'Safety Features',
            description: 'Panic mode for emergency navigation and Telegram alarm notifications'
        }
    ];

    const specs = [
        { label: 'Microcontroller', value: 'Arduino Uno Q' },
        { label: 'AI Model', value: 'Google Gemini 3 Flash/Pro' },
        { label: 'Dimensions', value: '24cm × 12cm × 10cm' },
        { label: 'Movement', value: '360° Differential Drive' },
        { label: 'Sensors', value: 'Ultrasonic + Thermo + Camera' },
        { label: 'Power', value: 'PowerBank 10000 mAh' },
    ];

    const costs = [
        { component: 'Arduino Uno Q', description: 'Main microcontroller', cost: 44 },
        { component: '2 × SG90 9g Servos', description: 'Wheel motors (360°)', cost: 4 },
        { component: '2 × SG90 9g Servos', description: 'Arm motors (180°)', cost: 4 },
        { component: 'Webcam', description: 'USB camera for vision', cost: 3 },
        { component: 'USB Dongle', description: 'Adapter for connectivity', cost: 3 },
        { component: 'Ultrasonic Sensor', description: 'Distance measurement', cost: 1.5 },
        { component: 'Bluetooth Speaker', description: 'Audio output', cost: 2.5 },
        { component: 'Breadboard & Wires', description: 'Prototyping components', cost: 5 },
        { component: '3D Printing Plastic', description: '~200g for case/mounts', cost: 3 },
        { component: 'Xiaomi Powerbank', description: '10000 mAh for power', cost: 10 },
    ];

    const totalCost = costs.reduce((sum, item) => sum + item.cost, 0);

    return (
        <div className="landing-page">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-background"></div>
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="hero-content"
                    >
                        <div className="hero-badge">
                            <Zap size={16} />
                            <span>Powered by Google Gemini AI</span>
                        </div>

                        <h1 className="hero-title">
                            AGI Robot
                        </h1>

                        <p className="hero-subtitle">
                            A fully autonomous, LLM-powered mobile robot using Google Gemini for real-time
                            decision-making, navigation, and human interaction
                        </p>

                        <div className="hero-buttons">
                            <Link to="/dashboard" className="btn btn-primary">
                                <span>Open Dashboard</span>
                                <ArrowRight size={20} />
                            </Link>
                            <Link to="/blog" className="btn btn-secondary">
                                <MessageSquare size={20} />
                                <span>Robot Diary</span>
                            </Link>
                            <a
                                href="https://github.com/msveshnikov/Arduino"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-secondary"
                            >
                                <Github size={20} />
                                <span>View on GitHub</span>
                            </a>
                        </div>
                    </motion.div>
                    <br /><br /><br /><br /><br />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="hero-image"
                    >
                        <div className="image-wrapper animate-float">
                            {heroImages.map((image, index) => (
                                <img
                                    key={index}
                                    src={image}
                                    alt={`AGI Robot ${index + 1}`}
                                    className="robot-image"
                                    style={{
                                        position: index === 0 ? 'relative' : 'absolute',
                                        top: 0,
                                        left: 0,
                                        width: '100%',
                                        height: '100%',
                                        opacity: currentImageIndex === index ? 1 : 0,
                                        transition: 'opacity 0.5s ease-in-out'
                                    }}
                                />
                            ))}
                            <div className="image-glow"></div>
                            <div className="carousel-indicators">
                                {heroImages.map((_, index) => (
                                    <button
                                        key={index}
                                        className={`indicator ${currentImageIndex === index ? 'active' : ''}`}
                                        onClick={() => setCurrentImageIndex(index)}
                                        aria-label={`View image ${index + 1}`}
                                    />
                                ))}
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <section className="section features-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="section-header text-center"
                    >
                        <h2>Key Features</h2>
                        <p className="section-description">
                            Advanced capabilities powered by artificial intelligence and modern robotics
                        </p>
                    </motion.div>

                    <div className="grid grid-3">
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: index * 0.1 }}
                                className="glass-card feature-card"
                            >
                                <div className="feature-icon">
                                    {feature.icon}
                                </div>
                                <h3 className="feature-title">{feature.title}</h3>
                                <p className="feature-description">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Specifications Section */}
            <section className="section specs-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="specs-grid"
                    >
                        <div className="specs-content">
                            <h2>Technical Specifications</h2>
                            <p className="section-description">
                                Built with Arduino Uno Q and powered by cutting-edge AI technology
                            </p>

                            <div className="specs-list">
                                {specs.map((spec, index) => (
                                    <motion.div
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ duration: 0.5, delay: index * 0.1 }}
                                        className="spec-item"
                                    >
                                        <span className="spec-label">{spec.label}</span>
                                        <span className="spec-value">{spec.value}</span>
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        <div className="specs-image">
                            <img src="/image-2.jpg" alt="Robot Hardware" />
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Cost Breakdown Section */}
            <section className="section cost-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="section-header text-center"
                    >
                        <h2>Project Cost</h2>
                        <p className="section-description">
                            Affordable DIY robotics - total investment just <span className="text-gradient">${totalCost}</span>
                        </p>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="glass-card cost-table-wrapper"
                    >
                        <table className="cost-table">
                            <thead>
                                <tr>
                                    <th>Component</th>
                                    <th>Description</th>
                                    <th>Cost (USD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {costs.map((item, index) => (
                                    <motion.tr
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ duration: 0.4, delay: index * 0.05 }}
                                    >
                                        <td className="component-name">{item.component}</td>
                                        <td className="component-desc">{item.description}</td>
                                        <td className="component-cost">${item.cost}</td>
                                    </motion.tr>
                                ))}
                                {/* <tr className="total-row">
                                    <td colSpan="2"><strong>Total Project Cost</strong></td>
                                    <td><strong className="text-gradient">${totalCost}</strong></td>
                                </tr> */}
                            </tbody>
                        </table>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.4 }}
                        className="api-cost-info text-center"
                    >
                        <h3>LLM API Running Cost</h3>
                        <p className="section-description">
                            The robot's consciousness operates in an autonomous loop powered by Gemini AI
                        </p>
                        <div className="api-cost-grid">
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="api-cost-item"
                            >
                                <span className="api-cost-label">Loop Duration</span>
                                <span className="api-cost-value">~20s</span>
                            </motion.div>
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="api-cost-item"
                            >
                                <span className="api-cost-label">Cost per Loop</span>
                                <span className="api-cost-value">$0.005</span>
                            </motion.div>
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="api-cost-item"
                            >
                                <span className="api-cost-label">Cost per Hour</span>
                                <span className="api-cost-value">$1</span>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Pricing Section */}
            <section className="section pricing-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="section-header text-center"
                    >
                        <h2>Choose Your Path</h2>
                        <p className="section-description">
                            Join the waitlist for the first batch of AGI Robots. No payment required now.
                        </p>
                    </motion.div>

                    <div className="pricing-grid">
                        {/* Plan 1: DIY */}
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5 }}
                            className={`glass-card pricing-card ${selectedPlan === 'Free' ? 'featured' : ''}`}
                            onClick={() => setSelectedPlan('Free')}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="pricing-header">
                                <h3 className="pricing-name">DIY Enthusiast</h3>
                                <div className="pricing-price">Free<span>/ ($80 parts)</span></div>
                            </div>
                            <ul className="pricing-features">
                                <li><Check size={18} /> <span>3D Print Files (STL)</span></li>
                                <li><Check size={18} /> <span>Complete Parts List</span></li>
                                <li><Check size={18} /> <span>Assembly Guide</span></li>
                                <li><Check size={18} /> <span>Source Code Access</span></li>
                            </ul>
                            <button
                                className={`btn ${selectedPlan === 'Free' ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setSelectedPlan('Free')}
                            >
                                {selectedPlan === 'Free' ? 'Selected' : 'Select Plan'}
                            </button>
                        </motion.div>

                        {/* Plan 2: Full Set */}
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className={`glass-card pricing-card ${selectedPlan === '$200' ? 'featured' : ''}`}
                            onClick={() => setSelectedPlan('$200')}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="pricing-header">
                                <h3 className="pricing-name">Full Detail Set</h3>
                                <div className="pricing-price">$200<span>/set</span></div>
                            </div>
                            <ul className="pricing-features">
                                <li><Check size={18} /> <span>All Hardware Components</span></li>
                                <li><Check size={18} /> <span>3D Printed Parts Included</span></li>
                                <li><Check size={18} /> <span>Personal Mobile App</span></li>
                                <li><Check size={18} /> <span>Priority Support</span></li>
                            </ul>
                            <button
                                className={`btn ${selectedPlan === '$200' ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setSelectedPlan('$200')}
                            >
                                {selectedPlan === '$200' ? 'Selected' : 'Select Plan'}
                            </button>
                        </motion.div>

                        {/* Plan 3: Assembled */}
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className={`glass-card pricing-card ${selectedPlan === '$300' ? 'featured' : ''}`}
                            onClick={() => setSelectedPlan('$300')}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="featured-badge">Best Value</div>
                            <div className="pricing-header">
                                <h3 className="pricing-name">Assembled Robot</h3>
                                <div className="pricing-price">$300<span>/unit</span></div>
                            </div>
                            <ul className="pricing-features">
                                <li><Check size={18} /> <span>Fully Assembled & Tested</span></li>
                                <li><Check size={18} /> <span>Personal Mobile App</span></li>
                                <li><Check size={18} /> <span>50 Hours Thinking Included</span></li>
                                <li><Check size={18} /> <span>White-glove Setup</span></li>
                            </ul>
                            <button
                                className={`btn ${selectedPlan === '$300' ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setSelectedPlan('$300')}
                            >
                                {selectedPlan === '$300' ? 'Selected' : 'Select Plan'}
                            </button>
                        </motion.div>
                    </div>

                    {/* Waitlist Form */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        className="glass-card waitlist-form"
                    >
                        <h3>Join the Waitlist</h3>
                        <p className="text-muted">Selected Plan: <span className="text-gradient" style={{ fontWeight: 700 }}>{
                            selectedPlan === 'Free' ? 'DIY Enthusiast' :
                                selectedPlan === '$200' ? 'Full Detail Set' : 'Assembled Robot'
                        }</span></p>

                        <form onSubmit={handleJoinWaitlist} className="waitlist-input-group">
                            <input
                                type="email"
                                placeholder="Enter your email"
                                className="waitlist-input"
                                value={waitlistEmail}
                                onChange={(e) => setWaitlistEmail(e.target.value)}
                                required
                            />
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? 'Joining...' : 'Secure My Spot'}
                            </button>
                        </form>

                        {submitStatus === 'success' && (
                            <div className="waitlist-success-msg animate-fade-in">
                                Success! We will contact you asap when we are ready for shipping.
                            </div>
                        )}
                        {submitStatus === 'error' && (
                            <div className="waitlist-error-msg animate-fade-in" style={{ color: '#ef4444', marginTop: '1rem' }}>
                                Something went wrong. Please try again later.
                            </div>
                        )}

                        <p className="waitlist-note">
                            * No credit card required. We just collect emails to gauge interest.
                        </p>
                    </motion.div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="section cta-section">
                <div className="container">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="glass-card cta-card"
                    >
                        <h2>Ready to Control the Robot?</h2>
                        <p className="cta-description">
                            Access the real-time dashboard to monitor telemetry, control movements,
                            and interact with the AGI system
                        </p>
                        <div className="hero-buttons" style={{ justifyContent: 'center', marginTop: '2rem' }}>
                            <Link to="/dashboard" className="btn btn-primary btn-large">
                                <span>Open Dashboard</span>
                                <ArrowRight size={24} />
                            </Link>
                            <Link to="/blog" className="btn btn-secondary btn-large">
                                <MessageSquare size={24} />
                                <span>Read Robot Diary</span>
                            </Link>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <div className="container">
                    <div className="footer-content">
                        <div className="footer-section">
                            <h3 className="text-gradient">AGI Robot</h3>
                            <p>Autonomous LLM-powered mobile robot</p>
                        </div>
                        <div className="footer-section">
                            <h4>Technology</h4>
                            <ul>
                                <li><a href="https://deepmind.google/technologies/gemini/" target="_blank" rel="noopener noreferrer">Google Gemini AI</a></li>
                                <li><a href="https://www.arduino.cc/" target="_blank" rel="noopener noreferrer">Arduino Uno Q</a></li>
                                <li><a href="https://en.wikipedia.org/wiki/Computer_vision" target="_blank" rel="noopener noreferrer">Computer Vision</a></li>
                                <li><a href="https://en.wikipedia.org/wiki/Natural_language_processing" target="_blank" rel="noopener noreferrer">Natural Language Processing</a></li>
                            </ul>
                        </div>
                        <div className="footer-section">
                            <h4>Links</h4>
                            <ul>
                                <li><a href="https://github.com/msveshnikov/Arduino" target="_blank" rel="noopener noreferrer">GitHub Repository</a></li>
                                <li><Link to="/dashboard">Dashboard</Link></li>
                                <li><Link to="/blog">Robot Diary</Link></li>
                            </ul>
                        </div>
                    </div>
                    <div className="footer-bottom">
                        <p>&copy; 2026 MaxSoft. Built with passion for AI and robotics.</p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
