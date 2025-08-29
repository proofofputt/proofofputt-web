import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiGetAllFundraisers } from '@/api';
import { format } from 'date-fns';
import '../components/Fundraising.css';

const ProgressBar = ({ raised, goal }) => {
  const percentage = goal > 0 ? Math.min((raised / goal) * 100, 100) : 0;
  return (
    <div className="progress-bar-container">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${percentage}%` }}></div>
      </div>
      <div className="progress-text">
        ${raised.toFixed(2)} / ${goal.toFixed(2)}
      </div>
    </div>
  );
};

const FundraisingPage = () => {
  const [fundraisers, setFundraisers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFundraisers = async () => {
      try {
        setLoading(true);
        const data = await apiGetAllFundraisers();
        setFundraisers(data);
      } catch (err) {
        setError('Failed to load fundraising campaigns.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchFundraisers();
  }, []);

  return (
    <div className="fundraising-page">
      <header className="page-header">
        <h2>Fundraising Campaigns</h2>
        <Link to="/fundraisers/new" className="btn">
          Create A Fundraiser
        </Link>
      </header>

      <div className="fundraiser-list-container">
        <div className="fundraiser-table">
          <div className="fundraiser-table-header">
            <span>Campaign</span>
            <span>Organizer</span>
            <span>Starts</span>
            <span>Ends</span>
            <span>Progress</span>
            <span /> {/* Empty header for view button column */}
          </div>
          {loading && <p style={{ padding: '2rem', textAlign: 'center' }}>Loading campaigns...</p>}
          {error && <p className="error-message" style={{ padding: '2rem', textAlign: 'center' }}>{error}</p>}
          {!loading && !error && fundraisers.map(f => (
            <div key={f.fundraiser_id} className="fundraiser-table-row">
              <div className="fundraiser-name-cause">
                <span className="fundraiser-name">{f.name}</span>
                <span className="fundraiser-cause">For: {f.cause}</span>
              </div>
              <span>{f.player_name}</span>
              <span>{format(new Date(f.start_time), 'MMM d, yyyy')}</span>
              <span>{format(new Date(f.end_time), 'MMM d, yyyy')}</span>
              <ProgressBar raised={f.amount_raised} goal={f.goal_amount} />
              <div className="action-cell">
                <Link to={`/fundraisers/${f.fundraiser_id}`}>
                  <button className="btn btn-yellow">View</button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FundraisingPage;
