import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiGetCareerStats } from '@/api.js';
import '@/components/PlayerCareerPage.css';

const PlayerCareerPage = () => {
    const { playerId } = useParams();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoading(true);
                const careerStats = await apiGetCareerStats(playerId);
                setStats(careerStats);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, [playerId]);

    if (loading) return <div className="container">Loading career stats...</div>;
    if (error) return <div className="container error-message">{error}</div>;
    if (!stats) return <div className="container">No stats available for this player.</div>;

    // Placeholder for the main stats tables
    const renderStatsTables = () => (
        <div className="stats-split-grid">
            <table className="career-stats-table">
                <thead>
                    <tr>
                        <th>Overall Performance</th>
                        <th>All-Time Best</th>
                        <th>All-Time Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Total Makes</td><td>{stats.high_makes}</td><td>{stats.sum_makes}</td></tr>
                    <tr><td>Best Streak</td><td>{stats.high_best_streak}</td><td>-</td></tr>
                    <tr><td>Fastest 21 Makes</td><td>{stats.low_fastest_21 || 'N/A'}</td><td>-</td></tr>
                </tbody>
            </table>
            <table className="career-stats-table">
                <thead>
                    <tr>
                        <th>Averages & Rates</th>
                        <th>All-Time Best</th>
                        <th>Career Avg.</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Makes Per Minute</td><td>{stats.high_mpm.toFixed(2)}</td><td>{stats.avg_mpm.toFixed(2)}</td></tr>
                    <tr><td>Accuracy</td><td>{stats.high_accuracy.toFixed(2)}%</td><td>{stats.avg_accuracy.toFixed(2)}%</td></tr>
                    <tr><td>Session Duration</td><td>{(stats.high_duration / 60).toFixed(2)} min</td><td>{(stats.sum_duration / 60).toFixed(2)} min</td></tr>
                </tbody>
            </table>
        </div>
    );

    return (
        <div className="container career-stats-page">
            <div className="page-header">
                <h2>{stats.player_name}'s Career Stats</h2>
            </div>

            {!stats.is_subscribed ? (
                <div className="upgrade-prompt">
                    <h3>Full Career Stats are a Subscriber Perk</h3>
                    <p>Upgrade to a full subscription to unlock your complete career statistics and history.</p>
                    <Link to="/settings" className="btn">Upgrade Now</Link>
                </div>
            ) : (
                <>
                    {renderStatsTables()}

                    <div className="summary-tables-grid">
                        <div className="summary-table-container">
                            <h3>Duels</h3>
                            <table className="career-stats-table">
                                <tbody>
                                    <tr><td>Active</td><td>{stats.duel_counts?.active ?? 0}</td></tr>
                                    <tr><td>Complete</td><td>{stats.duel_counts?.complete ?? 0}</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div className="summary-table-container">
                            <h3>Leagues</h3>
                            <table className="career-stats-table">
                                <tbody>
                                    <tr><td>Active</td><td>{stats.league_counts?.active ?? 0}</td></tr>
                                    <tr><td>Complete</td><td>{stats.league_counts?.complete ?? 0}</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default PlayerCareerPage;
