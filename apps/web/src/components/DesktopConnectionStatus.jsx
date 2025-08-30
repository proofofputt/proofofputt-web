import React, { useState, useEffect } from 'react';
import './ConnectionStatus.css';

const DesktopConnectionStatus = ({ onConnectionChange }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('checking');

  useEffect(() => {
    const checkConnection = () => {
      if (window.__TAURI__) {
        // Desktop app is running and web view is embedded
        setIsConnected(true);
        setConnectionState('connected');
      } else {
        // Running in browser - desktop app not connected
        setIsConnected(false);
        setConnectionState('browser');
      }
      onConnectionChange?.(isConnected);
    };

    checkConnection();
    // Check periodically in case desktop app is launched
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, [isConnected, onConnectionChange]);

  if (connectionState === 'connected') {
    return (
      <div className="connection-status connected">
        <span className="status-indicator">🟢</span>
        <span>Desktop App Connected - Ready for sessions</span>
      </div>
    );
  }

  return (
    <div className="connection-status disconnected">
      <div className="status-header">
        <span className="status-indicator">🔴</span>
        <span>Desktop App Required</span>
      </div>
      <div className="status-message">
        <p>To start sessions and calibrate your camera, you need the desktop application.</p>
        <div className="action-buttons">
          <a href="/download" className="btn btn-primary">Download Desktop App</a>
          <button className="btn btn-secondary" onClick={() => window.location.reload()}>
            Check Connection
          </button>
        </div>
        <div className="help-text">
          <details>
            <summary>Need help connecting?</summary>
            <ol>
              <li>Download and install the Proof of Putt desktop app</li>
              <li>Launch the desktop application</li>
              <li>The desktop app will open this web interface automatically</li>
              <li>Session controls will become available</li>
            </ol>
          </details>
        </div>
      </div>
    </div>
  );
};

export default DesktopConnectionStatus;