import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Blog from './pages/Blog';
import AssemblyGuide from './pages/AssemblyGuide';
import './index.css';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/blog" element={<Blog />} />
                <Route path="/assembly-guide" element={<AssemblyGuide />} />
            </Routes>
        </Router>
    );
}

export default App;
