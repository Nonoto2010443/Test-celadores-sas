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
      const response = await axios.post(`${API}/exam/generate`);
      setExam(response.data);
      // Initialize answers object
      const initialAnswers = {};
      response.data.preguntas.forEach((q) => {
        initialAnswers[q.id] = null;
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Error generating exam:', error);
      alert('Error al generar el examen');
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-white text-lg">Cargando examen...</p>
        </div>
      </div>
    );
  }

  if (!exam) return null;

  const question = exam.preguntas[currentQuestion];

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header with Timer */}
        <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-800">Examen de Celadores SAS</h2>
              <p className="text-gray-600">
                Pregunta {currentQuestion + 1} de {exam.preguntas.length} | Respondidas: {getAnsweredCount()}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${timeRemaining < 600 ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                  <Clock className="w-5 h-5" />
                  <span className="font-mono text-xl font-bold">{formatTime(timeRemaining)}</span>
                </div>
              </div>
            </div>
          </div>
          {timeRemaining < 600 && (
            <div className="mt-4 flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-semibold">¡Quedan menos de 10 minutos!</span>
            </div>
          )}
        </Card>

        {/* Question Card */}
        <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl p-8 mb-6">
          <div className="mb-6">
            {question.tema && (
              <span className="inline-block bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                {question.tema}
              </span>
            )}
            <h3 className="text-xl font-bold text-gray-800 leading-relaxed">
              {currentQuestion + 1}. {question.pregunta}
            </h3>
          </div>

          {/* Options */}
          <div className="space-y-3">
            {question.opciones.map((opcion, index) => {
              const isSelected = answers[question.id] === index;
              return (
                <button
                  key={index}
                  data-testid={`option-${index}`}
                  onClick={() => handleAnswerSelect(question.id, index)}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                    }`}>
                      {isSelected && <div className="w-3 h-3 bg-white rounded-full" />}
                    </div>
                    <span className="text-gray-800 leading-relaxed">
                      <strong>{String.fromCharCode(65 + index)}.</strong> {opcion}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {/* Navigation */}
        <div className="flex items-center justify-between gap-4">
          <Button
            onClick={() => setCurrentQuestion((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-xl disabled:opacity-50"
          >
            ← Anterior
          </Button>

          <div className="flex gap-2">
            {currentQuestion < exam.preguntas.length - 1 ? (
              <Button
                onClick={() => setCurrentQuestion((prev) => prev + 1)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl"
              >
                Siguiente →
              </Button>
            ) : (
              <Button
                onClick={handleSubmitExam}
                disabled={submitting}
                data-testid="submit-exam-button"
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-xl disabled:opacity-50"
              >
                {submitting ? 'Enviando...' : 'Finalizar Examen'}
              </Button>
            )}
          </div>
        </div>

        {/* Question Navigator */}
        <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl p-6 mt-6">
          <h4 className="font-bold text-gray-800 mb-4">Navegador de Preguntas</h4>
          <div className="grid grid-cols-10 gap-2">
            {exam.preguntas.map((q, index) => {
              const isAnswered = answers[q.id] !== null;
              const isCurrent = index === currentQuestion;
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(index)}
                  className={`w-10 h-10 rounded-lg font-semibold transition-all ${
                    isCurrent
                      ? 'bg-blue-600 text-white shadow-lg scale-110'
                      : isAnswered
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
          <div className="flex items-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border-2 border-green-500 rounded" />
              <span className="text-gray-600">Respondida</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-100 border-2 border-gray-300 rounded" />
              <span className="text-gray-600">Sin responder</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-600 rounded" />
              <span className="text-gray-600">Actual</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ExamPage;