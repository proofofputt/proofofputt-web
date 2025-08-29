import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext.jsx';
import { apiUpdatePlayerName, apiUpdatePlayerTimezone, apiUpdatePlayerSocials, apiRedeemCoupon, apiCancelSubscription } from '@/api.js';
import ChangePassword from '@/components/ChangePassword.jsx'; // Assuming this component exists and handles its own state
import './SettingsPage.css';

const SettingsPage = () => {
  const { playerData, refreshData, showNotification } = useAuth();
  const [name, setName] = useState('');
  const [timezone, setTimezone] = useState('');
  const [socials, setSocials] = useState({
    x_url: '',
    tiktok_url: '',
    website_url: '',
  });
  const [couponCode, setCouponCode] = useState('');
  const [showChangePassword, setShowChangePassword] = useState(false);

  // Safely populate state from playerData when it becomes available.
  // This prevents the component from crashing on initial render.
  useEffect(() => {
    if (playerData) {
      // This log confirms that playerData is now loaded and the component can safely access its properties.
      console.log('DEBUG: SettingsPage successfully loaded with playerData. Subscription Status:', playerData.subscription_status);
      setName(playerData.player_name || '');
      setTimezone(playerData.timezone || 'UTC');
      setSocials({
        x_url: playerData.x_url || '',
        tiktok_url: playerData.tiktok_url || '',
        website_url: playerData.website_url || '',
      });
    }
  }, [playerData]);

  const handleInfoSubmit = async (e) => {
    e.preventDefault();
    try {
      // Combine API calls for better efficiency
      await apiUpdatePlayerName(playerData.player_id, name);
      await apiUpdatePlayerTimezone(playerData.player_id, timezone);
      showNotification('Profile info updated successfully!');
      await refreshData();
    } catch (err) {
      showNotification(`Error: ${err.message}`, true);
    }
  };

  const handleSocialsSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiUpdatePlayerSocials(playerData.player_id, socials);
      showNotification('Social links updated successfully!');
      await refreshData();
    } catch (err) {
      showNotification(`Error: ${err.message}`, true);
    }
  };

  const handleSocialsChange = (e) => {
    const { name, value } = e.target;
    setSocials((prev) => ({ ...prev, [name]: value }));
  };

  const handleRedeemCoupon = async (e) => {
    e.preventDefault();
    if (!couponCode.trim()) {
      showNotification('Please enter a coupon code.', true);
      return;
    }
    try {
      const response = await apiRedeemCoupon(playerData.player_id, couponCode.trim());
      showNotification(response.message);
      setCouponCode('');
      await refreshData(); // Refresh after clearing state
    } catch (err) {
      showNotification(`Error: ${err.message}`, true);
    }
  };

  const handleCancelSubscription = async () => {
    if (window.confirm('Are you sure you want to cancel your subscription? You will lose access to premium features.')) {
      try {
        // Use a centralized API function instead of a hardcoded fetch
        const response = await apiCancelSubscription(playerData.player_id);
        showNotification(response.message);
        await refreshData();
      } catch (err) {
        showNotification(`Error: ${err.message}`, true);
      }
    }
  };

  return (
    <div className="settings-page">
      <h2>Settings</h2>
      {!playerData ? (
        <div className="settings-section">Loading settings...</div>
      ) : (
        <>
          <div className="settings-grid">
            <div className="settings-section">
              <h3>Account Information</h3>
              <form onSubmit={handleInfoSubmit}>
                <div className="form-group">
                  <label>Email</label>
                  <input type="email" value={playerData.player_email} disabled />
                </div>
                <div className="form-group">
                  <label>Display Name</label>
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Timezone</label>
                  <input type="text" value={timezone} onChange={(e) => { console.log('Timezone change event:', e); setTimezone(e.target.value); }} />
                  <p className="form-hint">e.g., "America/New_York", "UTC"</p>
                </div>
                <button type="submit" className="btn">Save Account Info</button>
              </form>
            </div>

            <div className="settings-section">
              <h3>Social Links</h3>
              <form onSubmit={handleSocialsSubmit}>
                <div className="form-group"><label>X (Twitter)</label><input type="url" name="x_url" value={socials.x_url} onChange={handleSocialsChange} placeholder="https://x.com/yourprofile" /></div>
                <div className="form-group"><label>TikTok</label><input type="url" name="tiktok_url" value={socials.tiktok_url} onChange={handleSocialsChange} placeholder="https://tiktok.com/@yourprofile" /></div>
                <div className="form-group"><label>Website</label><input type="url" name="website_url" value={socials.website_url} onChange={handleSocialsChange} placeholder="https://yourwebsite.com" /></div>
                <button type="submit" className="btn">Save Social Links</button>
              </form>
            </div>

            <div className="settings-section">
              <h3>Security</h3>
              <button onClick={() => setShowChangePassword(true)} className="btn-secondary">Change Password</button>
            </div>
          </div>

          {showChangePassword && <ChangePassword onClose={() => setShowChangePassword(false)} />}

          <div className="settings-section full-width-section">
            <h3>Manage Subscription</h3>
            {playerData.subscription_status === 'active' ? (
              <div className="subscription-status">
                <p><strong>Status:</strong> <span className="status-badge status-active">Full Subscriber</span></p>
                <p>Thank you for being a full subscriber! You have access to all features.</p>
                <button onClick={handleCancelSubscription} className="btn btn-danger">Cancel My Subscription</button>
              </div>
            ) : (
              <div className="upgrade-section">
                <p><strong>Status:</strong> <span className="status-badge status-free">Free Tier</span></p>
                <p>Upgrade to a full subscription to unlock all features and take your game to the next level.</p>
                <div className="features-grid">
                  <div className="feature-card free-tier">
                    <h3>Free Tier</h3>
                    <ul>
                      <li>✓ Camera Calibration & Session Recording</li>
                      <li>✓ View Your Most Recent Session</li>
                      <li>✓ Participate in Duels</li>
                      <li>✓ Join & Compete in Leagues</li>
                    </ul>
                  </div>
                  <div className="feature-card subscriber-tier">
                    <h3>Full Subscriber</h3>
                    <ul>
                      <li>✓ All Free Features</li>
                      <li>✓ Full Session History & Analysis</li>
                      <li>✓ Access to In-depth Career Stats</li>
                      <li>✓ AI-Powered Coach</li>
                      <li>✓ Create Leagues & Duels</li>
                      <li>✓ Create Fundraisers</li>
                    </ul>
                  </div>
                </div>
                <div className="upgrade-action">
                  <form onSubmit={handleRedeemCoupon} className="coupon-form">
                    <label htmlFor="coupon-input">Have an Early Access Code?</label>
                    <input id="coupon-input" type="text" value={couponCode} onChange={(e) => setCouponCode(e.target.value)} placeholder="Enter Code" className="coupon-input" />
                    <button type="submit" className="btn">Redeem</button>
                  </form>
                  <span className="or-divider">OR</span>
                  {/* This link should come from your Zaprite product settings */}
                  <a href="https://zaprite.com/p/proofofputt/subscription-link" target="_blank" rel="noopener noreferrer" className="btn">
                    Upgrade to Full Subscription ($2.10/mo)
                  </a>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default SettingsPage;