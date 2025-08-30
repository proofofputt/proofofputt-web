import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext.jsx';
import { useNotification } from '@/context/NotificationContext.jsx';
import { apiStartSession, apiStartCalibration } from '@/api.js';

const SessionControls = ({ isDesktopConnected }) => {
  const { playerData } = useAuth();
  const { showTemporaryNotification: showNotification } = useNotification();
  const [actionError, setActionError] = useState('');

  const handleStartSessionClick = async () => {
    if (!isDesktopConnected) {
      showNotification('Please open the desktop application to start sessions', true);
      return;
    }

    setActionError('');
    try {
      if (window.__TAURI__) {
        try {
          const { invoke } = await import('@tauri-apps/api/tauri');
          await invoke('start_session', { playerId: playerData.player_id });
          showNotification('Session started! Check the desktop application.');
        } catch (importErr) {
          console.error('Failed to import Tauri API:', importErr);
          showNotification('Desktop app integration not available', true);
        }
      } else {
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
        try {
          const { invoke } = await import('@tauri-apps/api/tauri');
          await invoke('start_calibration', { playerId: playerData.player_id });
          showNotification('Calibration started! Check the desktop application.');
        } catch (importErr) {
          console.error('Failed to import Tauri API:', importErr);
          showNotification('Desktop app integration not available', true);
        }
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
    <div className="session-controls-buttons" style={{ display: 'flex', gap: '1rem' }}>
      <button 
        onClick={handleStartSessionClick} 
        className={`btn btn-tertiary ${hasCalibration ? 'btn-orange' : ''}`}
        disabled={!isDesktopConnected}
        title={!isDesktopConnected ? "Requires desktop app" : ""}
      >
        Start New Session
      </button>
      <button 
        onClick={handleCalibrateClick} 
        className={`btn btn-tertiary ${!hasCalibration ? 'btn-orange' : 'btn-secondary'}`}
        disabled={!isDesktopConnected}
        title={!isDesktopConnected ? "Requires desktop app" : ""}
      >
        Calibrate Camera
      </button>
      {actionError && <p className="error-message">{actionError}</p>}
    </div>
  );
};

export default SessionControls;