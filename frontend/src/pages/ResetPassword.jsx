import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import './Auth.css';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    // Get token from URL
    const tokenFromUrl = searchParams.get('token');
    if (!tokenFromUrl) {
      setError('Token inválido. Por favor, solicita un nuevo enlace de recuperación.');
    } else {
      setToken(tokenFromUrl);
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    // Validations
    if (newPassword.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/auth/reset-password`, {
        token,
        new_password: newPassword
      });
      
      setMessage(response.data.message);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al restablecer la contraseña');
    } finally {
      setLoading(false);
    }
  };

  if (!token && !error) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Preparación Oposiciones SAS</h1>
          <h2>Celadores</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h3>Restablecer Contraseña</h3>

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
              <p style={{ margin: '10px 0 0 0', fontSize: '0.9rem' }}>
                Redirigiendo al inicio de sesión...
              </p>
            </div>
          )}

          {!message && token && (
            <>
              <div className="form-group">
                <label htmlFor="newPassword">Nueva Contraseña</label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Mínimo 6 caracteres"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirmar Nueva Contraseña</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Repite tu contraseña"
                  disabled={loading}
                />
              </div>

              <button 
                type="submit" 
                className="auth-button"
                disabled={loading}
              >
                {loading ? 'Restableciendo...' : 'Restablecer Contraseña'}
              </button>
            </>
          )}

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

export default ResetPassword;
