import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SubscriptionResult.css';

const SubscriptionCancel = () => {
  const navigate = useNavigate();

  return (
    <div className="subscription-result-container">
      <div className="subscription-result-card">
        <div className="cancel-icon">ℹ️</div>
        <h2>Suscripción Cancelada</h2>
        <p className="cancel-message">
          Has cancelado el proceso de suscripción. No se ha realizado ningún cargo.
        </p>
        <p>
          Puedes volver a intentarlo cuando estés listo.
        </p>
        <div className="action-buttons">
          <button 
            onClick={() => navigate('/pricing')} 
            className="action-button primary"
          >
            Ver Precios de Nuevo
          </button>
          <button 
            onClick={() => navigate('/dashboard')} 
            className="action-button secondary"
          >
            Volver al Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionCancel;
