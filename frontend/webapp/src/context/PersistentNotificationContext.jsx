import React, { createContext, useState, useContext, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext.jsx';
import {
  apiGetNotifications,
  apiGetUnreadNotificationsCount,
  apiMarkNotificationAsRead,
  apiMarkAllNotificationsAsRead,
  apiDeleteNotification,
} from '@/api.js';

const PersistentNotificationContext = createContext();

export const usePersistentNotifications = () => useContext(PersistentNotificationContext);

export const PersistentNotificationProvider = ({ children }) => {
  const { playerData } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchUnreadCount = useCallback(async () => {
    if (!playerData) return;
    try {
      const data = await apiGetUnreadNotificationsCount(playerData.player_id);
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error("Failed to fetch unread notifications count:", err);
    }
  }, [playerData]);

  const fetchNotifications = useCallback(async (limit = 20, offset = 0) => {
    if (!playerData) return;
    setIsLoading(true);
    try {
      const data = await apiGetNotifications(playerData.player_id, limit, offset);
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      setError('Failed to load notifications.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [playerData]);

  useEffect(() => {
    // Fetch initial count for the header badge when player data is available
    if (playerData) {
      fetchUnreadCount();
    }
  }, [playerData, fetchUnreadCount]);

  const markAsRead = async (notificationId) => {
    try {
      await apiMarkNotificationAsRead(notificationId, playerData.player_id);
      setNotifications(prev => prev.map(n => (n.id === notificationId ? { ...n, read_status: true } : n)));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiMarkAllNotificationsAsRead(playerData.player_id);
      setNotifications(prev => prev.map(n => ({ ...n, read_status: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all notifications as read:", err);
    }
  };

  const deleteNotification = async (notificationId) => {
    const originalNotifications = [...notifications];
    const notificationToDelete = notifications.find(n => n.id === notificationId);
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
    if (notificationToDelete && !notificationToDelete.read_status) {
        setUnreadCount(prev => Math.max(0, prev - 1));
    }
    try {
      await apiDeleteNotification(notificationId, playerData.player_id);
    } catch (err) {
      console.error("Failed to delete notification:", err);
      setNotifications(originalNotifications); // Revert on failure
    }
  };

  const value = { notifications, unreadCount, isLoading, error, fetchNotifications, markAsRead, markAllAsRead, deleteNotification, fetchUnreadCount };

  return (
    <PersistentNotificationContext.Provider value={value}>
      {children}
    </PersistentNotificationContext.Provider>
  );
};