import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext.jsx';
import { useNotification } from '@/context/NotificationContext.jsx';
import { apiStartSession, apiStartCalibration, apiGetCalibrationStatus } from '@/api.js';

const SessionControls = ({ isDesktopConnected }) => {
  const { playerData } = useAuth();
  const { showTemporaryNotification: showNotification } = useNotification();
  const [actionError, setActionError] = useState('');
  const [calibrationStatus, setCalibrationStatus] = useState(null);
  const [isCheckingCalibration, setIsCheckingCalibration] = useState(false);

  // Check calibration status when component mounts or desktop connection changes
  useEffect(() => {
    const checkCalibration = async () => {
      if (!playerData?.player_id || !isDesktopConnected) {
        setCalibrationStatus(null);
        return;
      }

      setIsCheckingCalibration(true);
      try {
        const status = await apiGetCalibrationStatus(playerData.player_id);
        setCalibrationStatus(status);
      } catch (error) {
        console.error('Failed to check calibration status:', error);
        setCalibrationStatus({ is_calibrated: false });
      } finally {
        setIsCheckingCalibration(false);
      }
    };

    checkCalibration();
  }, [playerData?.player_id, isDesktopConnected]);

  const handleStartSessionClick = async () => {
    if (!isDesktopConnected) {
      showNotification('Please open the desktop application to start sessions', true);
      return;
    }

    if (!playerData?.player_id) {
      showNotification('Player ID not available. Please refresh the page.', true);
      return;
    }

    setActionError('');
    try {
      // Always use web API endpoints - Tauri commands are only for when web runs inside desktop app
      await apiStartSession(playerData.player_id);
      showNotification('Session request sent to desktop application.');
    } catch (err) {
      console.error('Session start error:', err);
      setActionError(err.message);
      showNotification(err.message, true);
    }
  };

  const handleCalibrateClick = async () => {
    if (!isDesktopConnected) {
      showNotification('Please open the desktop application to calibrate', true);
      return;
    }

    if (!playerData?.player_id) {
      showNotification('Player ID not available. Please refresh the page.', true);
      return;
    }

    setActionError('');
    try {
      // Always use web API endpoints - Tauri commands are only for when web runs inside desktop app
      await apiStartCalibration(playerData.player_id);
      showNotification('Calibration request sent to desktop application.');
    } catch (err) {
      console.error('Calibration error:', err);
      setActionError(err.message);
      showNotification(err.message, true);
    }
  };

  const isCalibrated = calibrationStatus?.is_calibrated;
  const showCalibrationInfo = isDesktopConnected && calibrationStatus && !isCheckingCalibration;

  return (
    <div className="session-controls-buttons" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button 
          onClick={handleStartSessionClick} 
          className={`btn btn-tertiary ${isCalibrated ? 'btn-orange' : ''}`}
          disabled={!isDesktopConnected || !isCalibrated}
          title={
            !isDesktopConnected ? "Requires desktop app" :
            !isCalibrated ? "Camera must be calibrated first" : 
            "Start a new putting session"
          }
        >
          Start New Session
        </button>
        <button 
          onClick={handleCalibrateClick} 
          className={`btn btn-tertiary ${!isCalibrated ? 'btn-orange' : 'btn-secondary'}`}
          disabled={!isDesktopConnected}
          title={!isDesktopConnected ? "Requires desktop app" : "Calibrate camera for accurate tracking"}
        >
          {isCheckingCalibration ? 'Checking...' : 'Calibrate Camera'}
        </button>
      </div>
      
      {showCalibrationInfo && (
        <div style={{ fontSize: '0.9em', color: '#666' }}>
          {isCalibrated ? (
            <span>✅ Camera calibrated on {new Date(calibrationStatus.calibration_date).toLocaleDateString()}</span>
          ) : (
            <span>⚠️ Camera not calibrated. Please calibrate before starting sessions.</span>
          )}
        </div>
      )}
      
      {actionError && <p className="error-message">{actionError}</p>}
    </div>
  );
};

export default SessionControls;