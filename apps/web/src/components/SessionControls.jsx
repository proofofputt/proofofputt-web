import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext.jsx';
import { useNotification } from '@/context/NotificationContext.jsx';
import { apiStartSession, apiStartCalibration } from '@/api.js';
import DesktopConnectionStatus from './DesktopConnectionStatus.jsx';
import './ConnectionStatus.css';

const SessionControls = () => {
  const { playerData } = useAuth();
  const { showTemporaryNotification: showNotification } = useNotification();
  const [isDesktopConnected, setIsDesktopConnected] = useState(false);
  const [actionError, setActionError] = useState('');

  const handleStartSessionClick = async () => {
    if (!isDesktopConnected) {
      showNotification('Please open the desktop application to start sessions', true);
      return;
    }

    setActionError('');
    try {
      if (window.__TAURI__) {
        const { invoke } = await import('@tauri-apps/api/tauri');
        await invoke('start_session', { playerId: playerData.player_id });
        showNotification('Session started! Check the desktop application.');
      } else {
        // This shouldn't happen if isDesktopConnected is false, but fallback
        await apiStartSession(playerData.player_id);
        showNotification('Session request sent to desktop application.');
      }
    } catch (err) {
      setActionError(err.message);
      showNotification(err.message, true);
    }
  };

  const handleCalibrateClick = async () => {
    if (!isDesktopConnected) {
      showNotification('Please open the desktop application to calibrate', true);
      return;
    }

    setActionError('');
    try {
      if (window.__TAURI__) {
        const { invoke } = await import('@tauri-apps/api/tauri');
        await invoke('start_calibration', { playerId: playerData.player_id });
        showNotification('Calibration started! Check the desktop application.');
      } else {
        await apiStartCalibration(playerData.player_id);
        showNotification('Calibration request sent to desktop application.');
      }
    } catch (err) {
      setActionError(err.message);
      showNotification(err.message, true);
    }
  };

  const hasCalibration = playerData?.calibration_data;

  return (
    <div className="session-controls">
      <DesktopConnectionStatus onConnectionChange={setIsDesktopConnected} />
      
      <div className="desktop-actions">
        <h3>Session Controls</h3>
        {isDesktopConnected ? (
          <div className="action-buttons">
            <button 
              onClick={handleStartSessionClick} 
              className={`btn ${hasCalibration ? 'btn-orange' : ''}`}
            >
              Start New Session
            </button>
            <button 
              onClick={handleCalibrateClick} 
              className={`btn ${!hasCalibration ? 'btn-orange' : 'btn-secondary'}`}
            >
              Calibrate Camera
            </button>
          </div>
        ) : (
          <div className="disabled-actions">
            <button className="btn btn-disabled" disabled title="Requires desktop app">
              Start New Session
            </button>
            <button className="btn btn-disabled" disabled title="Requires desktop app">
              Calibrate Camera
            </button>
            <p className="help-text">
              💡 <strong>Tip:</strong> Session tracking happens through the desktop application. 
              This web interface displays your results and statistics.
            </p>
          </div>
        )}
        {actionError && <p className="error-message">{actionError}</p>}
      </div>
    </div>
  );
};

export default SessionControls;