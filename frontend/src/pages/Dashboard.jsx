import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadDashboardData();
    loadSubscriptionStatus();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load statistics
      const statsResponse = await axios.get(`${API_URL}/api/results/stats/me`);
      setStats(statsResponse.data);
      
      // Load history
      const historyResponse = await axios.get(`${API_URL}/api/results/history/me`);
      setHistory(historyResponse.data.resultados || []);
      
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSubscriptionStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/subscription/status`);
      setSubscriptionStatus(response.data.subscription_status);
    } catch (error) {
      console.error('Error loading subscription:', error);
    }
  };

  const handleNewExam = () => {
    // Check subscription before allowing exam
    if (subscriptionStatus !== 'active') {
      if (window.confirm('Necesitas una suscripción activa para realizar exámenes. ¿Deseas ver los planes de suscripción?')) {
        navigate('/pricing');
      }
      return;
    }
    navigate('/exam');
  };

  const handleViewResult = (resultId) => {
    navigate(`/results/${resultId}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Prepare chart data (last 10 exams)
  const chartData = history.slice(0, 10).reverse().map((result, index) => ({
    name: `Examen ${history.length - 9 + index}`,
    puntuacion: result.puntuacion
  }));

  if (loading) {
    return (
      <div className="dashboard-loading">
        <p>Cargando datos...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Panel de Control - Celadores SAS</h1>
          <div className="header-actions">
            <span className="welcome-text">Hola, {user?.nombre}</span>
            <button onClick={handleLogout} className="logout-btn">
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Stats Cards */}
        <section className="stats-section">
          <h2>Estadísticas Generales</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-content">
                <h3>Total Exámenes</h3>
                <p className="stat-value">{stats?.total_examenes || 0}</p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⭐</div>
              <div className="stat-content">
                <h3>Mejor Puntuación</h3>
                <p className="stat-value">{stats?.mejor_puntuacion?.toFixed(1) || 0}</p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📈</div>
              <div className="stat-content">
                <h3>Promedio</h3>
                <p className="stat-value">{stats?.promedio_puntuacion?.toFixed(1) || 0}</p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <h3>Tiempo Promedio</h3>
                <p className="stat-value">{stats?.tiempo_promedio_minutos?.toFixed(0) || 0} min</p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-content">
                <h3>Total Correctas</h3>
                <p className="stat-value">{stats?.total_correctas || 0}</p>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">❌</div>
              <div className="stat-content">
                <h3>Total Incorrectas</h3>
                <p className="stat-value">{stats?.total_incorrectas || 0}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Chart */}
        {chartData.length > 0 && (
          <section className="chart-section">
            <h2>Progreso (Últimos 10 Exámenes)</h2>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="puntuacion" 
                    stroke="#667eea" 
                    strokeWidth={3}
                    dot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {/* New Exam Button */}
        <section className="action-section">
          <button onClick={handleNewExam} className="new-exam-btn">
            🎯 Comenzar Nuevo Examen
          </button>
        </section>

        {/* History */}
        <section className="history-section">
          <h2>Historial de Exámenes</h2>
          {history.length === 0 ? (
            <div className="empty-history">
              <p>Aún no has realizado ningún examen.</p>
              <button onClick={handleNewExam} className="start-first-exam-btn">
                Realizar mi primer examen
              </button>
            </div>
          ) : (
            <div className="history-table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Puntuación</th>
                    <th>Correctas</th>
                    <th>Incorrectas</th>
                    <th>En Blanco</th>
                    <th>Tiempo</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((result) => (
                    <tr key={result.id}>
                      <td>
                        {format(new Date(result.fecha_completado), 'dd MMM yyyy, HH:mm', { locale: es })}
                      </td>
                      <td>
                        <span className={`score ${result.puntuacion >= 60 ? 'good' : 'bad'}`}>
                          {result.puntuacion.toFixed(1)}
                        </span>
                      </td>
                      <td>{result.correctas}</td>
                      <td>{result.incorrectas}</td>
                      <td>{result.en_blanco}</td>
                      <td>{Math.round(result.tiempo_empleado_segundos / 60)} min</td>
                      <td>
                        <button 
                          onClick={() => handleViewResult(result.id)}
                          className="view-btn"
                        >
                          Ver Detalles
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
