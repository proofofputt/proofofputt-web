import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext.jsx';

const ProtectedRoute = ({ children }) => {
  const { playerData, isLoading } = useAuth();

  if (isLoading) {
    // Optional: Show a loading spinner while checking auth status
    return <div>Loading...</div>;
  }

  if (!playerData) {
    // If not authenticated, redirect to the login page
    return <Navigate to="/login" replace />;
  }

  // If authenticated, render the child component that was passed in
  return children;
};

export default ProtectedRoute;