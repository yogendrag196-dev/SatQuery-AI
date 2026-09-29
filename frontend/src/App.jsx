import React, { useState, useEffect } from 'react';
import SplashScreen from './components/SplashScreen';
import './components/SplashScreen.css';

/**
 * App.jsx
 * Top-level application wrapper for SatQuery AI.
 * Handles single-session splash screen playback before Ground Station login.
 */
export default function App() {
  const [showSplash, setShowSplash] = useState(() => {
    return !sessionStorage.getItem('sq_splash_shown');
  });

  const handleSplashFinish = () => {
    sessionStorage.setItem('sq_splash_shown', '1');
    setShowSplash(false);
    if (window.satQueryApp) {
      window.satQueryApp.setView('auth');
    }
  };

  return (
    <>
      {showSplash && <SplashScreen onFinish={handleSplashFinish} />}
    </>
  );
}
