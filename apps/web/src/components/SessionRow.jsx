import React from 'react';
import { format } from 'date-fns';

const DetailCategory = ({ title, overview, detailed }) => {
  const overviewEntries = Object.entries(overview);
  // Sort overview entries by count, descending.
  const sortedOverview = overviewEntries.sort(([, countA], [, countB]) => countB - countA);
  // Sort detailed entries by count, descending.
  const sortedDetailed = Object.entries(detailed).sort(([, countA], [, countB]) => countB - countA);

  return (
    <div className="details-section">
      <h4>{title}</h4>

      <h5>Overview</h5>
      {sortedOverview.length > 0 ? (
        <ul>
          {sortedOverview.map(([key, value]) => (
            <li key={key}>
              <strong>{key}:</strong> {value}
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ fontStyle: 'italic', opacity: 0.7 }}>None</p>
      )}

      <h5 style={{ marginTop: '1rem' }}>Detailed Classification</h5>
      {sortedDetailed.length > 0 ? (
        <ul>
          {sortedDetailed.map(([key, value]) => (
            <li key={key}>
              <strong>{key}:</strong> {value}
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ fontStyle: 'italic', opacity: 0.7 }}>None</p>
      )}
    </div>
  );
};

const SessionRow = ({ session, playerTimezone, isLocked, isExpanded, onToggleExpand }) => {
  const formatDate = (dateString, timezone) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString); // Parse ISO 8601 string directly
    if (isNaN(date.getTime())) {
        console.error("Invalid date value for formatting:", dateString);
        return 'N/A'; // Or handle as per UI needs
    }
    const options = {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short',
      timeZone: timezone,
    };
    return new Intl.DateTimeFormat('en-US', options).format(date);
  };

  const formatStat = (value, suffix = '') => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      if (value % 1 !== 0) {
        return `${value.toFixed(2)}${suffix}`;
      }
    }
    return `${value}${suffix}`;
  }

  // Safely parse JSON data from the session
  const parseJsonData = (jsonString) => {
    if (!jsonString) return null;
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      console.error("Failed to parse session JSON data:", e);
      return null;
    }
  };

  const makesByCategory = parseJsonData(session.makes_by_category);
  const missesByCategoryFromDB = parseJsonData(session.misses_by_category);
  const puttList = parseJsonData(session.putt_list);

  // --- Calculate Makes Categories ---
  const makesOverview = { TOP: 0, RIGHT: 0, LOW: 0, LEFT: 0 };
  const makesDetailed = {};
  if (makesByCategory) {
    for (const [classification, count] of Object.entries(makesByCategory)) {
      // Populate overview
      if (classification.includes('TOP')) makesOverview.TOP += count;
      if (classification.includes('RIGHT')) makesOverview.RIGHT += count;
      if (classification.includes('LOW')) makesOverview.LOW += count;
      if (classification.includes('LEFT')) makesOverview.LEFT += count;
      // Populate detailed
      makesDetailed[classification] = count;
    }
  }

  // --- Calculate Misses Categories ---
  const missesOverviewDefaults = { RETURN: 0, CATCH: 0, TIMEOUT: 0, 'QUICK PUTT': 0 };
  const missesOverview = { ...missesOverviewDefaults, ...missesByCategoryFromDB };
  const missesDetailed = {};
  if (puttList) {
    const missPutts = puttList.filter(p => p['Putt Classification'] === 'MISS');
    for (const putt of missPutts) {
      // The detailed classification from the putt list includes "MISS - " which we can remove for cleaner display
      const detail = putt['Putt Detailed Classification'].replace('MISS - ', '');
      missesDetailed[detail] = (missesDetailed[detail] || 0) + 1;
    }
  }

  return (
    <>
      <tr
        onClick={() => !isLocked && onToggleExpand(session.session_id)}
        className={isExpanded ? 'is-expanded-parent' : ''}
        style={{ cursor: isLocked ? 'not-allowed' : 'pointer' }}
      >
        <td>
          <button
            onClick={(e) => {
              if (isLocked) return;
              e.stopPropagation();
              onToggleExpand(session.session_id);
            }}
            disabled={isLocked}
          >
            Details
          </button>
        </td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatDate(session.start_time, playerTimezone)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.session_duration / 60, 'm')}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.total_makes)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.total_misses)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.best_streak)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.fastest_21_makes, 's')}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.putts_per_minute)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.makes_per_minute)}</td>
        <td className={isLocked ? 'blurred-stat' : ''}>{formatStat(session.most_makes_in_60_seconds)}</td>
      </tr>
      {isExpanded && !isLocked && (
        <tr className="session-details-row">
          <td colSpan="10">
            <div className="session-details-content">
              <h3>Session Details</h3>
              <div className="details-grid">
                <DetailCategory title="Makes By Category" overview={makesOverview} detailed={makesDetailed} />
                <DetailCategory title="Misses By Category" overview={missesOverview} detailed={missesDetailed} />
                <div className="details-section">
                  <h4>Consecutive by Category</h4>
                  <ul>
                    {Object.entries({
                      "3": "Three:",
                      "7": "Seven:",
                      "10": "Ten:",
                      "15": "Fifteen:",
                      "21": "Twenty-One:",
                      "50": "Fifty:",
                      "100": "One Hundred:"
                    }).map(([category, label]) => (
                      <li key={category}>
                        <strong>{label}</strong> {session.consecutive_by_category?.[category] || 0}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

export default SessionRow;