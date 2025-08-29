import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
// import { AuthContext } from '../context/AuthContext'; // Assuming an AuthContext exists
import { apiLogin } from '../api';
import './LoginPage.css';

const LoginPage = () => {
  // const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!email || !password) {
      setError('Please enter both email and password.');
      setLoading(false);
      return;
    }

    try {
      const data = await apiLogin(email, password);

      // Assuming the login function in AuthContext handles storing user data and token
      // login(data);
      console.log("Login successful, navigating to dashboard.", data); // Placeholder for context login

      // Redirect to the dashboard upon successful login
      navigate('/dashboard');

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-form-container">
        <h2>Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="login-form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
          {error && <p className="login-error-message">{error}</p>}
        </form>
        <div className="login-links">
          <Link to="/reset-password">Forgot Password?</Link>
          <span>|</span>
          <Link to="/register">Don't have an account? Sign Up</Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
