import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './Auth.css';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/auth/forgot-password`, {
        email
      });
      
      setMessage(response.data.message);
      setEmail(''); // Clear form
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al enviar el correo');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Preparación Oposiciones SAS</h1>
          <h2>Celadores</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h3>Recuperar Contraseña</h3>
          
          <p style={{ color: '#666', fontSize: '0.95rem', marginBottom: '20px' }}>
            Introduce tu email y te enviaremos un enlace para restablecer tu contraseña.
          </p>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {message && (
            <div style={{
              backgroundColor: '#d4edda',
              color: '#155724',
              padding: '12px',
              borderRadius: '8px',
              marginBottom: '20px',
              border: '1px solid #c3e6cb'
            }}>
              {message}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="tu@email.com"
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Enviando...' : 'Enviar Enlace de Recuperación'}
          </button>

          <div className="auth-footer">
            <p>
              <Link to="/login">Volver al inicio de sesión</Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;
