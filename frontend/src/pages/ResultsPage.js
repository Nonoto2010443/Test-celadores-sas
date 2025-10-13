import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Home, CheckCircle2, XCircle, Clock, Award, ChevronRight } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ResultsPage = () => {
  const { examId } = useParams();
  const navigate = useNavigate();
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExamResults();
  }, [examId]);

  const fetchExamResults = async () => {
    try {
      const response = await axios.get(`${API}/exams/${examId}`);
      setExam(response.data);
    } catch (error) {
      console.error("Error fetching results:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Cargando resultados...</p>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>No se encontraron resultados.</p>
      </div>
    );
  }

  const totalPreguntas = exam.preguntas.length;
  const correctas = exam.correctas || 0;
  const incorrectas = exam.incorrectas || 0;
  const enBlanco = exam.en_blanco || 0;
  const puntuacionOficial = exam.puntuacion_oficial || 0;
  const puntuacionSobre100 = exam.puntuacion_sobre_100 || 0;

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} seg`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-4">Resultados del Examen</h1>
          <p className="text-slate-600">Revisa tu rendimiento y aprende de tus respuestas</p>
        </div>

        {/* Score Overview */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
            <CardContent className="p-6 text-center">
              <Award className="h-8 w-8 mx-auto mb-2" />
              <div className="text-4xl font-bold mb-1" data-testid="score">{puntuacionSobre100.toFixed(2)}</div>
              <div className="text-sm opacity-90">Puntuación sobre 100</div>
              <div className="text-2xl font-bold mt-2">{puntuacionOficial.toFixed(2)}/{totalPreguntas}</div>
              <div className="text-xs opacity-75 mt-1">Puntuación oficial</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="p-6 text-center">
              <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-600" />
              <div className="text-4xl font-bold text-green-600 mb-1" data-testid="correct-count">{correctas}</div>
              <div className="text-sm text-slate-600">Correctas</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="p-6 text-center">
              <XCircle className="h-8 w-8 mx-auto mb-2 text-red-600" />
              <div className="text-4xl font-bold text-red-600 mb-1" data-testid="incorrect-count">{incorrectas}</div>
              <div className="text-sm text-slate-600">Incorrectas</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="p-6 text-center">
              <Clock className="h-8 w-8 mx-auto mb-2 text-blue-600" />
              <div className="text-2xl font-bold text-blue-600 mb-1" data-testid="time-used">{formatTime(exam.tiempo_usado)}</div>
              <div className="text-sm text-slate-600">Tiempo usado</div>
            </CardContent>
          </Card>
        </div>

        {/* Progress Bars */}
        <Card className="mb-8 border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Desglose de Respuestas</CardTitle>
            <p className="text-sm text-slate-600 mt-2">
              Sistema oficial SAS: Correctas (+2 pts) - Incorrectas (-0.5 pts) - En blanco (0 pts)
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Correctas (+2 puntos cada una)</span>
                <span className="font-semibold text-green-600">{correctas} ({((correctas/totalPreguntas)*100).toFixed(0)}%)</span>
              </div>
              <Progress value={(correctas/totalPreguntas)*100} className="h-3 bg-green-100" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Incorrectas (-0.5 puntos cada una)</span>
                <span className="font-semibold text-red-600">{incorrectas} ({((incorrectas/totalPreguntas)*100).toFixed(0)}%)</span>
              </div>
              <Progress value={(incorrectas/totalPreguntas)*100} className="h-3 bg-red-100" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>En blanco (no puntúan)</span>
                <span className="font-semibold text-slate-600">{enBlanco} ({((enBlanco/totalPreguntas)*100).toFixed(0)}%)</span>
              </div>
              <Progress value={(enBlanco/totalPreguntas)*100} className="h-3 bg-slate-100" />
            </div>
            <div className="pt-4 border-t-2">
              <div className="flex justify-between items-center">
                <span className="font-bold">Total preguntas:</span>
                <span className="font-bold text-lg">{correctas + incorrectas + enBlanco} / {totalPreguntas}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Questions Review */}
        <Card className="mb-8 border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Revisión de Preguntas</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="all">
              <TabsList className="mb-6">
                <TabsTrigger value="all">Todas</TabsTrigger>
                <TabsTrigger value="incorrect">Incorrectas</TabsTrigger>
                <TabsTrigger value="correct">Correctas</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-6">
                {exam.preguntas.map((pregunta, index) => {
                  const userAnswer = exam.respuestas_usuario[index];
                  const isCorrect = userAnswer === pregunta.respuesta_correcta;
                  const isUnanswered = userAnswer === null;

                  return (
                    <div 
                      key={index} 
                      className={`p-6 rounded-lg border-2 ${
                        isUnanswered ? 'border-slate-300 bg-slate-50' :
                        isCorrect ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'
                      }`}
                      data-testid={`question-review-${index}`}
                    >
                      {/* Header con resultado */}
                      <div className="flex items-center justify-between mb-4 pb-3 border-b-2">
                        <div className="flex items-center gap-3">
                          {isUnanswered ? (
                            <>
                              <div className="w-10 h-10 rounded-full bg-slate-300 flex items-center justify-center">
                                <span className="text-slate-700 font-bold text-lg">?</span>
                              </div>
                              <div>
                                <p className="font-bold text-slate-700">Pregunta {index + 1}</p>
                                <p className="text-sm text-slate-600">Sin responder</p>
                              </div>
                            </>
                          ) : isCorrect ? (
                            <>
                              <CheckCircle2 className="h-10 w-10 text-green-600" />
                              <div>
                                <p className="font-bold text-green-700">Pregunta {index + 1} - ¡CORRECTA!</p>
                                <p className="text-sm text-green-600">Has acertado la respuesta</p>
                              </div>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-10 w-10 text-red-600" />
                              <div>
                                <p className="font-bold text-red-700">Pregunta {index + 1} - INCORRECTA</p>
                                <p className="text-sm text-red-600">Tu respuesta no es correcta</p>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Pregunta */}
                      <p className="font-semibold text-lg text-slate-900 mb-4">{pregunta.texto}</p>
                      
                      {/* Respuesta del usuario */}
                      {!isUnanswered && (
                        <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                          <p className="text-sm font-semibold text-blue-900 mb-1">Tu respuesta:</p>
                          <p className="text-blue-800">
                            <span className="font-bold mr-2">{String.fromCharCode(65 + userAnswer)}.</span>
                            {pregunta.opciones[userAnswer]}
                          </p>
                        </div>
                      )}
                      
                      {/* Opciones */}
                      <div className="space-y-3 mb-4">
                        <p className="text-sm font-semibold text-slate-700 mb-2">Opciones de respuesta:</p>
                        {pregunta.opciones.map((opcion, optIndex) => {
                          const isThisCorrect = optIndex === pregunta.respuesta_correcta;
                          const isUserChoice = optIndex === userAnswer;

                          return (
                            <div 
                              key={optIndex}
                              className={`p-4 rounded-lg border-2 ${
                                isThisCorrect ? 'bg-green-100 border-green-500' :
                                isUserChoice && !isThisCorrect ? 'bg-red-100 border-red-500' :
                                'bg-white border-slate-200'
                              }`}
                            >
                              <div className="flex items-start gap-2">
                                <span className="font-bold text-lg min-w-[30px]">{String.fromCharCode(65 + optIndex)}.</span>
                                <div className="flex-1">
                                  <p className={`${isThisCorrect ? 'text-green-900 font-semibold' : isUserChoice ? 'text-red-900' : 'text-slate-700'}`}>
                                    {opcion}
                                  </p>
                                  {isThisCorrect && (
                                    <div className="flex items-center gap-2 mt-2">
                                      <CheckCircle2 className="h-5 w-5 text-green-700" />
                                      <span className="text-green-700 font-bold text-sm">RESPUESTA CORRECTA</span>
                                    </div>
                                  )}
                                  {isUserChoice && !isThisCorrect && (
                                    <div className="flex items-center gap-2 mt-2">
                                      <XCircle className="h-5 w-5 text-red-700" />
                                      <span className="text-red-700 font-bold text-sm">Tu respuesta (incorrecta)</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Justificación */}
                      <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-lg">
                        <p className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                          <span className="text-lg">📚</span>
                          Justificación:
                        </p>
                        <p className="text-indigo-800 leading-relaxed">{pregunta.justificacion}</p>
                      </div>
                    </div>
                  );
                })}
              </TabsContent>

              <TabsContent value="incorrect" className="space-y-6">
                {exam.preguntas
                  .map((pregunta, index) => ({ pregunta, index }))
                  .filter(({ index }) => {
                    const userAnswer = exam.respuestas_usuario[index];
                    return userAnswer !== null && userAnswer !== exam.preguntas[index].respuesta_correcta;
                  })
                  .map(({ pregunta, index }) => {
                    const userAnswer = exam.respuestas_usuario[index];

                    return (
                      <div key={index} className="p-6 rounded-lg border-2 border-red-300 bg-red-50">
                        {/* Header */}
                        <div className="flex items-center gap-3 mb-4 pb-3 border-b-2 border-red-200">
                          <XCircle className="h-10 w-10 text-red-600" />
                          <div>
                            <p className="font-bold text-red-700">Pregunta {index + 1} - INCORRECTA</p>
                            <p className="text-sm text-red-600">Revisa la respuesta correcta</p>
                          </div>
                        </div>

                        {/* Pregunta */}
                        <p className="font-semibold text-lg text-slate-900 mb-4">{pregunta.texto}</p>
                        
                        {/* Tu respuesta */}
                        <div className="mb-4 p-4 bg-red-100 border-l-4 border-red-600 rounded">
                          <p className="text-sm font-bold text-red-900 mb-1">Tu respuesta (incorrecta):</p>
                          <p className="text-red-800 font-semibold">
                            <span className="font-bold mr-2">{String.fromCharCode(65 + userAnswer)}.</span>
                            {pregunta.opciones[userAnswer]}
                          </p>
                        </div>
                        
                        {/* Opciones */}
                        <div className="space-y-3 mb-4">
                          <p className="text-sm font-semibold text-slate-700 mb-2">Todas las opciones:</p>
                          {pregunta.opciones.map((opcion, optIndex) => {
                            const isThisCorrect = optIndex === pregunta.respuesta_correcta;
                            const isUserChoice = optIndex === userAnswer;

                            return (
                              <div 
                                key={optIndex}
                                className={`p-4 rounded-lg border-2 ${
                                  isThisCorrect ? 'bg-green-100 border-green-500' :
                                  isUserChoice ? 'bg-red-100 border-red-500' :
                                  'bg-white border-slate-200'
                                }`}
                              >
                                <div className="flex items-start gap-2">
                                  <span className="font-bold text-lg min-w-[30px]">{String.fromCharCode(65 + optIndex)}.</span>
                                  <div className="flex-1">
                                    <p className={`${isThisCorrect ? 'text-green-900 font-semibold' : isUserChoice ? 'text-red-900 font-semibold' : 'text-slate-700'}`}>
                                      {opcion}
                                    </p>
                                    {isThisCorrect && (
                                      <div className="flex items-center gap-2 mt-2">
                                        <CheckCircle2 className="h-5 w-5 text-green-700" />
                                        <span className="text-green-700 font-bold text-sm">RESPUESTA CORRECTA</span>
                                      </div>
                                    )}
                                    {isUserChoice && (
                                      <div className="flex items-center gap-2 mt-2">
                                        <XCircle className="h-5 w-5 text-red-700" />
                                        <span className="text-red-700 font-bold text-sm">Tu respuesta</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Justificación */}
                        <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-lg">
                          <p className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                            <span className="text-lg">📚</span>
                            Justificación:
                          </p>
                          <p className="text-indigo-800 leading-relaxed">{pregunta.justificacion}</p>
                        </div>
                      </div>
                    );
                  })}
                {exam.preguntas.filter((_, i) => {
                  const userAnswer = exam.respuestas_usuario[i];
                  return userAnswer !== null && userAnswer !== exam.preguntas[i].respuesta_correcta;
                }).length === 0 && (
                  <div className="text-center py-12 text-slate-600">
                    ¡Excelente! No tienes respuestas incorrectas.
                  </div>
                )}
              </TabsContent>

              <TabsContent value="correct" className="space-y-6">
                {exam.preguntas
                  .map((pregunta, index) => ({ pregunta, index }))
                  .filter(({ index }) => exam.respuestas_usuario[index] === exam.preguntas[index].respuesta_correcta)
                  .map(({ pregunta, index }) => (
                    <div key={index} className="p-6 rounded-lg border-2 border-green-300 bg-green-50">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-4 pb-3 border-b-2 border-green-200">
                        <CheckCircle2 className="h-10 w-10 text-green-600" />
                        <div>
                          <p className="font-bold text-green-700">Pregunta {index + 1} - ¡CORRECTA!</p>
                          <p className="text-sm text-green-600">Has respondido correctamente</p>
                        </div>
                      </div>

                      {/* Pregunta */}
                      <p className="font-semibold text-lg text-slate-900 mb-4">{pregunta.texto}</p>
                      
                      {/* Tu respuesta correcta */}
                      <div className="mb-4 p-4 bg-green-100 border-l-4 border-green-600 rounded">
                        <p className="text-sm font-bold text-green-900 mb-1 flex items-center gap-2">
                          <CheckCircle2 className="h-5 w-5" />
                          Tu respuesta (correcta):
                        </p>
                        <p className="text-green-800 font-semibold">
                          <span className="font-bold mr-2">{String.fromCharCode(65 + pregunta.respuesta_correcta)}.</span>
                          {pregunta.opciones[pregunta.respuesta_correcta]}
                        </p>
                      </div>

                      {/* Justificación */}
                      <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-lg">
                        <p className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                          <span className="text-lg">📚</span>
                          Justificación:
                        </p>
                        <p className="text-indigo-800 leading-relaxed">{pregunta.justificacion}</p>
                      </div>
                    </div>
                  ))}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-center gap-4">
          <Button
            onClick={() => navigate("/")}
            variant="outline"
            className="px-8 py-6 rounded-xl"
            data-testid="home-button"
          >
            <Home className="mr-2 h-5 w-5" />
            Volver al Inicio
          </Button>
          <Button
            onClick={() => navigate("/exam")}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6 rounded-xl"
            data-testid="new-exam-button"
          >
            Nuevo Examen
            <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
