import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import './Pricing.css';

const Pricing = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const origin = window.location.origin;
      
      const response = await axios.post(`${API_URL}/api/subscription/create-checkout`, {
        origin_url: origin
      });

      // Redirect to Stripe checkout
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (err) {
      console.error('Error creating checkout:', err);
      setError(err.response?.data?.detail || 'Error al crear la sesión de pago');
      setLoading(false);
    }
  };

  return (
    <div className="pricing-container">
      <div className="pricing-content">
        <div className="pricing-header">
          <h1>Preparación Oposiciones SAS</h1>
          <h2>Celadores</h2>
          <p className="pricing-subtitle">
            Prepárate con exámenes ilimitados y contenido actualizado
          </p>
        </div>

        <div className="pricing-card">
          <div className="pricing-badge">SUSCRIPCIÓN MENSUAL</div>
          
          <div className="pricing-price">
            <span className="currency">€</span>
            <span className="amount">10</span>
            <span className="period">/mes</span>
          </div>

          <div className="pricing-features">
            <h3>Incluye:</h3>
            <ul>
              <li>
                <span className="check-icon">✓</span>
                <span>Exámenes ilimitados de 50 preguntas</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Temporizador oficial de 90 minutos</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>16,510 preguntas oficiales del SAS</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Preguntas generadas por IA actualizada</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Sistema de puntuación oficial</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Historial completo de tus exámenes</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Estadísticas y gráficos de progreso</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Justificaciones detalladas</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Sin abreviaturas confusas</span>
              </li>
              <li>
                <span className="check-icon">✓</span>
                <span>Cancela cuando quieras</span>
              </li>
            </ul>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button 
            onClick={handleSubscribe}
            disabled={loading}
            className="subscribe-button"
          >
            {loading ? 'Procesando...' : 'Suscribirse Ahora'}
          </button>

          <p className="pricing-note">
            Pago seguro procesado por Stripe. Cancela en cualquier momento desde tu panel de control.
          </p>
        </div>

        {isAuthenticated && (
          <button 
            onClick={() => navigate('/dashboard')}
            className="back-button"
          >
            Volver al Dashboard
          </button>
        )}

        {!isAuthenticated && (
          <div className="pricing-footer">
            <p>
              ¿Ya tienes cuenta? <a href="/login">Inicia sesión</a>
            </p>
            <p>
              ¿No tienes cuenta? <a href="/register">Regístrate gratis</a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Pricing;
