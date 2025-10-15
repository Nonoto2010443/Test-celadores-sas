import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { CheckCircle2, XCircle, Circle, Trophy, Clock, Home } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ResultsPage = () => {
  const { resultId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchResult();
  }, [resultId]);

  const fetchResult = async () => {
    try {
      const resultResponse = await axios.get(`${API}/results/${resultId}`);
      const resultData = resultResponse.data;
      setResult(resultData);

      const examResponse = await axios.get(`${API}/exam/${resultData.exam_id}`);
      setExam(examResponse.data);
    } catch (error) {
      console.error('Error fetching result:', error);
      alert('Error al cargar los resultados');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getAnswerForQuestion = (questionId) => {
    return result.respuestas.find((r) => r.question_id === questionId);
  };

  const getScoreColor = (score) => {
    if (score >= 65) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreMessage = (score) => {
    if (score >= 65) return '¡Enhorabuena! Has superado el examen con éxito';
    if (score >= 40) return 'Necesitas más preparación. ¡No te rindas!';
    return 'Necesitas más preparación. ¡Sigue estudiando!';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-white text-lg">Cargando resultados...</p>
        </div>
      </div>
    );
  }

  if (!result || !exam) return null;

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl p-8 mb-6">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <Trophy className={`w-20 h-20 ${getScoreColor(result.puntuacion)}`} />
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Resultados del Examen
            </h1>
            <p className={`text-2xl font-bold ${getScoreColor(result.puntuacion)}`}>
              {getScoreMessage(result.puntuacion)}
            </p>
          </div>
        </Card>

        {/* Score Summary */}
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-xl p-6">
            <div className="text-center">
              <div className={`text-5xl font-bold mb-2 ${getScoreColor(result.puntuacion)}`}>
                {result.puntuacion}
              </div>
              <div className="text-gray-600 font-semibold">Puntuación Total</div>
              <div className="text-sm text-gray-500">sobre 100 puntos</div>
            </div>
          </Card>

          <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-xl p-6">
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <CheckCircle2 className="w-12 h-12 text-green-600" />
              </div>
              <div className="text-3xl font-bold text-green-600 mb-1">{result.correctas}</div>
              <div className="text-gray-600 font-semibold">Correctas</div>
              <div className="text-sm text-gray-500">+2 puntos cada una</div>
            </div>
          </Card>

          <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-xl p-6">
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <XCircle className="w-12 h-12 text-red-600" />
              </div>
              <div className="text-3xl font-bold text-red-600 mb-1">{result.incorrectas}</div>
              <div className="text-gray-600 font-semibold">Incorrectas</div>
              <div className="text-sm text-gray-500">-0.5 puntos cada una</div>
            </div>
          </Card>

          <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-xl p-6">
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <Circle className="w-12 h-12 text-gray-400" />
              </div>
              <div className="text-3xl font-bold text-gray-600 mb-1">{result.en_blanco}</div>
              <div className="text-gray-600 font-semibold">En Blanco</div>
              <div className="text-sm text-gray-500">0 puntos</div>
            </div>
          </Card>
        </div>

        {/* Time Stats */}
        <Card className="bg-white/95 backdrop-blur-sm shadow-xl rounded-xl p-6 mb-6">
          <div className="flex items-center justify-center gap-3">
            <Clock className="w-6 h-6 text-blue-600" />
            <span className="text-lg text-gray-700">
              Tiempo empleado: <strong className="text-blue-600">{formatTime(result.tiempo_empleado_segundos)}</strong>
            </span>
          </div>
        </Card>

        {/* Details Toggle */}
        <div className="flex justify-center gap-4 mb-6">
          <Button
            onClick={() => setShowDetails(!showDetails)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl"
          >
            {showDetails ? 'Ocultar Detalles' : 'Ver Respuestas Detalladas'}
          </Button>
          <Button
            onClick={() => navigate('/')}
            className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-xl"
          >
            <Home className="w-5 h-5 mr-2" />
            Nuevo Examen
          </Button>
        </div>

        {/* Detailed Results */}
        {showDetails && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">Respuestas Detalladas</h2>
            {exam.preguntas.map((question, index) => {
              const answer = getAnswerForQuestion(question.id);
              const isCorrect = answer?.selected_option === question.respuesta_correcta;
              const isBlank = answer?.selected_option === null;

              return (
                <Card
                  key={question.id}
                  className="bg-white/95 backdrop-blur-sm shadow-lg rounded-xl p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      {isBlank ? (
                        <Circle className="w-8 h-8 text-gray-400" />
                      ) : isCorrect ? (
                        <CheckCircle2 className="w-8 h-8 text-green-600" />
                      ) : (
                        <XCircle className="w-8 h-8 text-red-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="mb-3">
                        {question.tema && (
                          <span className="inline-block bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-semibold mb-2">
                            {question.tema}
                          </span>
                        )}
                        <h3 className="text-lg font-bold text-gray-800">
                          {index + 1}. {question.pregunta}
                        </h3>
                      </div>

                      <div className="space-y-2">
                        {question.opciones.map((opcion, optIndex) => {
                          const isSelected = answer?.selected_option === optIndex;
                          const isCorrectOption = optIndex === question.respuesta_correcta;

                          return (
                            <div
                              key={optIndex}
                              className={`p-3 rounded-lg border-2 ${
                                isCorrectOption
                                  ? 'border-green-500 bg-green-50'
                                  : isSelected
                                  ? 'border-red-500 bg-red-50'
                                  : 'border-gray-200'
                              }`}
                            >
                              <div className="flex items-start gap-2">
                                <span className="font-bold text-gray-700">
                                  {String.fromCharCode(65 + optIndex)}.
                                </span>
                                <span className="text-gray-800">{opcion}</span>
                                {isCorrectOption && (
                                  <span className="ml-auto text-green-600 font-semibold text-sm">
                                    ✓ Correcta
                                  </span>
                                )}
                                {isSelected && !isCorrectOption && (
                                  <span className="ml-auto text-red-600 font-semibold text-sm">
                                    Tu respuesta
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Justificación obligatoria */}
                      <div className="mt-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                        <p className="text-sm text-gray-700">
                          <strong className="text-blue-700">Justificación:</strong>{' '}
                          {question.explicacion || 'Consulta el temario oficial del SAS para más detalles sobre esta pregunta.'}
                        </p>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsPage;
