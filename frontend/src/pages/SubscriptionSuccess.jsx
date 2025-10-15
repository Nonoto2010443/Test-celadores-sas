import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import './SubscriptionResult.css';

const SubscriptionSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('checking'); // checking, success, error
  const [countdown, setCountdown] = useState(5);
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    
    if (!sessionId) {
      setStatus('error');
      return;
    }

    // Poll checkout status
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/subscription/checkout-status/${sessionId}`);
        
        if (response.data.payment_status === 'paid') {
          setStatus('success');
          
          // Start countdown
          const timer = setInterval(() => {
            setCountdown(prev => {
              if (prev <= 1) {
                clearInterval(timer);
                navigate('/dashboard');
                return 0;
              }
              return prev - 1;
            });
          }, 1000);
          
          return () => clearInterval(timer);
        }
      } catch (error) {
        console.error('Error checking status:', error);
        setStatus('error');
      }
    };

    // Check immediately
    checkStatus();
    
    // Poll every 2 seconds for up to 30 seconds
    let pollCount = 0;
    const pollInterval = setInterval(() => {
      pollCount++;
      if (pollCount > 15) {
        clearInterval(pollInterval);
        setStatus('error');
        return;
      }
      checkStatus();
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [searchParams, navigate, API_URL]);

  return (
    <div className="subscription-result-container">
      <div className="subscription-result-card">
        {status === 'checking' && (
          <>
            <div className="spinner-large"></div>
            <h2>Verificando tu pago...</h2>
            <p>Por favor espera mientras confirmamos tu suscripción</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <h2>¡Suscripción Activada!</h2>
            <p className="success-message">
              Tu pago ha sido procesado correctamente. Ya puedes acceder a todos los exámenes.
            </p>
            <div className="benefits-list">
              <h3>Ahora tienes acceso a:</h3>
              <ul>
                <li>✓ Exámenes ilimitados</li>
                <li>✓ 16,510 preguntas oficiales</li>
                <li>✓ Estadísticas y progreso</li>
                <li>✓ Historial completo</li>
              </ul>
            </div>
            <p className="redirect-message">
              Redirigiendo al dashboard en {countdown} segundos...
            </p>
            <button onClick={() => navigate('/dashboard')} className="action-button">
              Ir al Dashboard Ahora
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <h2>Error al Verificar el Pago</h2>
            <p className="error-message">
              No pudimos verificar tu suscripción. Por favor, contacta con soporte si el cargo fue realizado.
            </p>
            <button onClick={() => navigate('/dashboard')} className="action-button">
              Volver al Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSuccess;
