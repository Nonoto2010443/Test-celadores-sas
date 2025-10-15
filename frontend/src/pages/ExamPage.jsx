import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ExamPage.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

const ExamPage = () => {
  const navigate = useNavigate();
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(5400); // 90 minutes in seconds
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    generateExam();
  }, []);

  useEffect(() => {
    if (!exam) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmitExam();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [exam]);

  const generateExam = async () => {
    try {
      setLoading(true);
      // Set a longer timeout for exam generation (60 seconds)
      const response = await axios.post(`${API}/exam/generate`, {}, {
        timeout: 60000  // 60 seconds
      });
      setExam(response.data);
      // Initialize answers object
      const initialAnswers = {};
      response.data.preguntas.forEach((q) => {
        initialAnswers[q.id] = null;
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Error generating exam:', error);
      if (error.code === 'ECONNABORTED') {
        alert('El examen está tardando demasiado en generarse. Por favor, intenta de nuevo.');
      } else {
        alert('Error al generar el examen');
      }
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (questionId, optionIndex) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmitExam = async () => {
    if (submitting) return;

    const unansweredCount = Object.values(answers).filter((a) => a === null).length;
    if (unansweredCount > 0 && timeRemaining > 0) {
      const confirm = window.confirm(
        `Tienes ${unansweredCount} preguntas sin responder. ¿Estás seguro de enviar el examen?`
      );
      if (!confirm) return;
    }

    setSubmitting(true);
    try {
      const respuestas = Object.entries(answers).map(([question_id, selected_option]) => ({
        question_id,
        selected_option,
      }));

      const timeUsed = 5400 - timeRemaining;

      const response = await axios.post(`${API}/exam/submit`, {
        exam_id: exam.id,
        respuestas,
        tiempo_empleado_segundos: timeUsed,
      });

      navigate(`/results/${response.data.id}`);
    } catch (error) {
      console.error('Error submitting exam:', error);
      alert('Error al enviar el examen');
      setSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getAnsweredCount = () => {
    return Object.values(answers).filter((a) => a !== null).length;
  };

  if (loading) {
    return (
      <div className="exam-loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Generando examen...</p>
        </div>
      </div>
    );
  }

  if (!exam) return null;

  const question = exam.preguntas[currentQuestion];

  return (
    <div className="exam-container">
      <div className="exam-content">
        {/* Header with Timer */}
        <div className="exam-header">
          <div className="header-info">
            <h2>Examen de Celadores SAS</h2>
            <p>
              Pregunta {currentQuestion + 1} de {exam.preguntas.length} | Respondidas: {getAnsweredCount()}
            </p>
          </div>
          <div className="timer-container">
            <div className={`timer ${timeRemaining < 600 ? 'timer-warning' : ''}`}>
              <span className="timer-icon">⏱️</span>
              <span className="timer-text">{formatTime(timeRemaining)}</span>
            </div>
          </div>
          {timeRemaining < 600 && (
            <div className="time-warning">
              ⚠️ ¡Quedan menos de 10 minutos!
            </div>
          )}
        </div>

        {/* Question Card */}
        <div className="question-card">
          <div className="question-header">
            {question.tema && (
              <span className="question-tema">{question.tema}</span>
            )}
            <h3 className="question-text">
              {currentQuestion + 1}. {question.pregunta}
            </h3>
          </div>

          {/* Options */}
          <div className="options-container">
            {question.opciones.map((opcion, index) => {
              const isSelected = answers[question.id] === index;
              return (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(question.id, index)}
                  className={`option-button ${isSelected ? 'selected' : ''}`}
                >
                  <div className="option-content">
                    <div className={`option-radio ${isSelected ? 'selected' : ''}`}>
                      {isSelected && <div className="radio-dot" />}
                    </div>
                    <span className="option-text">
                      <strong>{String.fromCharCode(65 + index)}.</strong> {opcion}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation */}
        <div className="exam-navigation">
          <button
            onClick={() => setCurrentQuestion((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
            className="nav-button prev-button"
          >
            ← Anterior
          </button>

          <div className="nav-actions">
            {currentQuestion < exam.preguntas.length - 1 ? (
              <button
                onClick={() => setCurrentQuestion((prev) => prev + 1)}
                className="nav-button next-button"
              >
                Siguiente →
              </button>
            ) : (
              <button
                onClick={handleSubmitExam}
                disabled={submitting}
                className="nav-button submit-button"
              >
                {submitting ? 'Enviando...' : 'Finalizar Examen'}
              </button>
            )}
          </div>
        </div>

        {/* Question Navigator */}
        <div className="question-navigator">
          <h4>Navegador de Preguntas</h4>
          <div className="navigator-grid">
            {exam.preguntas.map((q, index) => {
              const isAnswered = answers[q.id] !== null;
              const isCurrent = index === currentQuestion;
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(index)}
                  className={`navigator-item ${isCurrent ? 'current' : ''} ${isAnswered ? 'answered' : ''}`}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
          <div className="navigator-legend">
            <div className="legend-item">
              <div className="legend-box answered" />
              <span>Respondida</span>
            </div>
            <div className="legend-item">
              <div className="legend-box unanswered" />
              <span>Sin responder</span>
            </div>
            <div className="legend-item">
              <div className="legend-box current" />
              <span>Actual</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExamPage;