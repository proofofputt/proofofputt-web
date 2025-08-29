import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Dashboard from '@/components/Dashboard.jsx';
import DuelsPage from '@/components/DuelsPage.jsx';
import SettingsPage from '@/components/SettingsPage.jsx';
import LeagueDetailPage from '@/components/LeagueDetailPage.jsx';
import LeaguesPage from '@/components/LeaguesPage.jsx';
import SessionHistoryPage from '@/components/SessionHistoryPage.jsx';
import PlayerCareerPage from '@/components/PlayerCareerPage.jsx';
import CoachPage from '@/components/CoachPage.jsx';
import FundraisingPage from '@/components/FundraisingPage.jsx';
import FundraiserCreatePage from '@/components/FundraiserCreatePage.jsx';
import PlayerVsPlayerPage from '@/components/PlayerVsPlayerPage.jsx';
import FundraiserDetailPage from '@/components/FundraiserDetailPage.jsx';
import NotificationsPage from '@/components/NotificationsPage.jsx';
import Header from '@/components/Header.jsx';
import { useAuth } from '@/context/AuthContext.jsx';
import { PersistentNotificationProvider } from './context/PersistentNotificationContext.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import LoginPage from './components/LoginPage.jsx';
import ResetPasswordPage from './components/ResetPasswordPage.jsx';
import './App.css';

const App = () => {
  const location = useLocation();
  const { playerData, isLoading } = useAuth();

  if (isLoading) {
    return <p style={{ textAlign: 'center', padding: '2rem' }}>Loading...</p>;
  }

  return (
    <div className="App">
      <PersistentNotificationProvider>
        {playerData && <Header />}
        <main className={location.pathname === '/coach' ? 'container-fluid' : 'container'}>
          <Routes>
            {/* Public Route */}
            <Route path="/login" element={<LoginPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Protected Routes */}
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/player/:playerId/sessions" element={<ProtectedRoute><SessionHistoryPage /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
            <Route path="/duels" element={<ProtectedRoute><DuelsPage /></ProtectedRoute>} />
            <Route path="/player/:playerId/stats" element={<ProtectedRoute><PlayerCareerPage /></ProtectedRoute>} />
            <Route path="/leagues/:leagueId" element={<ProtectedRoute><LeagueDetailPage /></ProtectedRoute>} />
            <Route path="/leagues" element={<ProtectedRoute><LeaguesPage /></ProtectedRoute>} />
            <Route path="/coach" element={<ProtectedRoute><CoachPage /></ProtectedRoute>} />
            <Route path="/coach/:conversationId" element={<ProtectedRoute><CoachPage /></ProtectedRoute>} />
            <Route path="/players/:player1Id/vs/:player2Id" element={<ProtectedRoute><PlayerVsPlayerPage /></ProtectedRoute>} />
            <Route path="/fundraisers" element={<ProtectedRoute><FundraisingPage /></ProtectedRoute>} />
            <Route path="/fundraisers/new" element={<ProtectedRoute><FundraiserCreatePage /></ProtectedRoute>} />
            <Route path="/fundraisers/:fundraiserId" element={<ProtectedRoute><FundraiserDetailPage /></ProtectedRoute>} />
            <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
          </Routes>
        </main>
      </PersistentNotificationProvider>
    </div>
  );
};

export default App;
