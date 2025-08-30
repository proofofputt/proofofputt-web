import React, { useState, useEffect } from 'react';
import './ConnectionStatus.css';

const DesktopConnectionStatus = ({ onConnectionChange }) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const checkConnection = () => {
      const connected = !!window.__TAURI__;
      setIsConnected(connected);
      onConnectionChange?.(connected);
    };

    checkConnection();
    // Check periodically in case desktop app is launched
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, [onConnectionChange]);

  if (isConnected) {
    return null; // Don't show anything when connected
  }

  const handleDownload = () => {
    // Open GitHub releases page for desktop app downloads
    window.open('https://github.com/proofofputt/app/releases', '_blank');
  };

  const handleCheckConnection = () => {
    // Force re-check connection status
    const checkConnection = () => {
      const connected = !!window.__TAURI__;
      setIsConnected(connected);
      onConnectionChange?.(connected);
      
      if (connected) {
        alert('Desktop app detected! Session controls are now available.');
      } else {
        alert('Desktop app not detected. Please ensure the desktop application is running and try again.');
      }
    };
    checkConnection();
  };

  return (
    <div className="connection-status disconnected">
      <div className="status-header">
        <span className="status-indicator">🔴</span>
        <span>Desktop App Required</span>
      </div>
      <p>To start sessions and calibrate your camera, you need the desktop application.</p>
      
      <div className="action-buttons">
        <button onClick={handleDownload} className="btn btn-primary">
          Download Desktop App
        </button>
        <button onClick={handleCheckConnection} className="btn btn-secondary">
          Check Connection
        </button>
      </div>
      
      <details className="help-details">
        <summary>Need help connecting?</summary>
        <ol>
          <li>Download and install the Proof of Putt desktop app</li>
          <li>Launch the desktop application</li>
          <li>The desktop app will open this web interface automatically</li>
          <li>Session controls will become available</li>
        </ol>
      </details>
    </div>
  );
};

export default DesktopConnectionStatus;