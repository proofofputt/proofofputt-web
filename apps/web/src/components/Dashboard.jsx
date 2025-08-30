import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext.jsx';
import SessionRow from '@/components/SessionRow.jsx';
import { useNotification } from '@/context/NotificationContext.jsx';
import { apiGetLeaderboards } from '@/api.js';
import DesktopConnectionStatus from '@/components/DesktopConnectionStatus.jsx';
import SessionControls from '@/components/SessionControls.jsx';
import LeaderboardCard from '@/components/LeaderboardCard.jsx';

const StatCard = ({ title, value }) => (
  <div className="stats-card">
    <h3>{title}</h3>
    <p className="stat-value">{value ?? 'N/A'}</p>
  </div>
);

function Dashboard() {
  const { playerData, refreshData } = useAuth();
  const { showTemporaryNotification: showNotification } = useNotification();
  const isSubscribed = playerData?.subscription_status === 'active';
  const [expandedSessionId, setExpandedSessionId] = useState(null);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [isDesktopConnected, setIsDesktopConnected] = useState(false);

  const handleConnectionChange = (connected) => {
    setIsDesktopConnected(connected);
  };
  const tableWrapperRef = useRef(null);

  // This effect manages the height of the session table container
  // to "lock" the view when a row is expanded.
  useEffect(() => {
    const wrapper = tableWrapperRef.current;
    if (!wrapper) return;

    if (expandedSessionId) {
      // A row is expanded. Find the key elements inside the container.
      const header = wrapper.querySelector('.session-table thead');
      const parentRow = wrapper.querySelector('.session-table tr.is-expanded-parent');
      const detailsRow = wrapper.querySelector('.session-table .session-details-row');

      if (header && parentRow && detailsRow) {
        // Calculate the exact height needed to show only these three elements.
        // Add a small 2px buffer for borders.
        const requiredHeight = header.offsetHeight + parentRow.offsetHeight + detailsRow.offsetHeight + 2;
        wrapper.style.maxHeight = `${requiredHeight}px`;

        // To fix the occlusion, programmatically scroll the container so the
        // expanded row is positioned just below the sticky header.
        wrapper.scrollTop = parentRow.offsetTop - header.offsetHeight;
      }
    } else {
      // No row is expanded, so reset the maxHeight to allow the CSS to
      // apply the default collapsed height.
      wrapper.style.maxHeight = null;
    }
  }, [expandedSessionId]); // This effect runs every time the expandedRowId changes

  useEffect(() => {
    const fetchLeaderboards = async () => {
        try {
            const data = await apiGetLeaderboards();
            setLeaderboardData(data);
        } catch (error) {
            console.error("Could not fetch leaderboard data:", error);
        }
    };

    fetchLeaderboards();
  }, []); // Empty dependency array means this runs once on mount

  const handleRefreshClick = () => {
    refreshData(playerData.player_id);
    showNotification('Data refreshed!');
  };

  const handleToggleExpand = (sessionId) => {
    setExpandedSessionId(prevId => (prevId === sessionId ? null : sessionId));
  };

  if (!playerData || !playerData.stats) {
    return <p>Loading player data...</p>;
  }

  const { stats, sessions } = playerData;

  const totalPutts = (stats.total_makes || 0) + (stats.total_misses || 0);
  const makePercentage = totalPutts > 0 ? ((stats.total_makes / totalPutts) * 100).toFixed(1) + '%' : 'N/A';

  return (
    <>
      <DesktopConnectionStatus onConnectionChange={handleConnectionChange} />
      
      <div className="dashboard-actions">
        <SessionControls isDesktopConnected={isDesktopConnected} />
        <button onClick={handleRefreshClick} className="btn btn-tertiary">Refresh Data</button>
      </div>

      <div className="stats-summary-bar">
        <h2>All-Time Stats</h2>
      </div>
      <div className="dashboard-grid">
        <StatCard title="Makes" value={stats.total_makes} />
        <StatCard title="Misses" value={stats.total_misses} />
        <StatCard title="Accuracy" value={makePercentage} />
        <StatCard title="Fastest 21" value={stats.fastest_21_makes ? `${stats.fastest_21_makes.toFixed(2)}s` : 'N/A'} />
      </div>
      
      <div className={`session-list-container ${expandedSessionId ? 'is-expanded' : ''}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Session History</h3>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to={`/player/${playerData.player_id}/stats`} className="btn btn-secondary">Career Stats</Link>
            <Link to={`/player/${playerData.player_id}/sessions`} className="btn btn-secondary">Full History</Link>
          </div>
        </div>
        <div className="session-table-wrapper" ref={tableWrapperRef}>
          <table className="session-table">
            <thead>
              <tr><th style={{ width: '120px' }}>Details</th><th>Session Date</th><th>Duration</th><th>Makes</th><th>Misses</th><th>Best Streak</th><th>Fastest 21</th><th>PPM</th><th>MPM</th><th>Most in 60s</th></tr>
            </thead>
            <tbody>
              {sessions && sessions.length > 0 ? (
                sessions.map((session, index) => (
                  <SessionRow
                    key={session.session_id}
                    session={session}
                    playerTimezone={playerData.timezone}
                    isLocked={!isSubscribed && index > 0}
                    isExpanded={expandedSessionId === session.session_id}
                    onToggleExpand={handleToggleExpand}
                  />
                ))
              ) : (
                <tr className="table-placeholder-row">
                    <td colSpan="10">No sessions recorded yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="leaderboard-container">
        <div className="leaderboard-summary-bar">
            <h2>Leaderboard</h2>
        </div>
        <div className="leaderboard-grid">
            {leaderboardData ? (
                <>
                    <LeaderboardCard title="Most Makes" leaders={leaderboardData.top_makes} />
                    <LeaderboardCard title="Best Streak" leaders={leaderboardData.top_streaks} />
                    <LeaderboardCard title="Makes/Min" leaders={leaderboardData.top_makes_per_minute} />
                    <LeaderboardCard title="Fastest 21" leaders={leaderboardData.fastest_21} />
                </>
            ) : (
                <p>Loading leaderboards...</p>
            )}
        </div>
      </div>

    </>
  );
}

export default Dashboard;
