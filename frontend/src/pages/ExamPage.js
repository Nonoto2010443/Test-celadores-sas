import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Clock, Loader2, AlertCircle, ChevronLeft, ChevronRight, Send } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const EXAM_DURATION = 90 * 60; // 90 minutes in seconds

const ExamPage = () => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [timeRemaining, setTimeRemaining] = useState(EXAM_DURATION);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    generateExam();
  }, []);

  useEffect(() => {
    if (questions.length === 0 || submitting) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          if (!submitting) {
            handleSubmit();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [questions.length]);

  const generateExam = async () => {
    try {
      setLoading(true);
      // Increased timeout to 120 seconds (2 minutes) for AI generation
      const response = await axios.post(`${API}/exams/generate`, {}, { timeout: 120000 });
      setQuestions(response.data);
      setAnswers(new Array(response.data.length).fill(null));
      toast.success("¡Examen generado exitosamente!");
    } catch (error) {
      console.error("Error generating exam:", error);
      toast.error("Error al generar el examen. Por favor, intenta de nuevo.");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (value) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = parseInt(value);
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    if (submitting) return;
    
    const timeUsed = EXAM_DURATION - timeRemaining;
    
    try {
      setSubmitting(true);
      const response = await axios.post(`${API}/exams/submit`, {
        preguntas: questions,
        respuestas_usuario: answers,
        tiempo_usado: timeUsed
      });
      
      toast.success("¡Examen enviado con éxito!");
      navigate(`/results/${response.data.id}`);
    } catch (error) {
      console.error("Error submitting exam:", error);
      toast.error("Error al enviar el examen. Por favor, intenta de nuevo.");
      setSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate answered count - React will re-render when answers changes
  // Use useMemo to ensure consistent calculation
  const answeredCount = answers.filter(a => a !== null).length;
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="text-center">
          <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Generando tu examen...</h2>
          <p className="text-slate-600">Creando 50 preguntas personalizadas con IA</p>
        </div>
      </div>
    );
  }

  const currentQ = questions[currentQuestion];

  // Safety check - if no current question, show error
  if (!currentQ) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Error al cargar la pregunta</h2>
          <p className="text-slate-600 mb-4">No se pudo cargar la pregunta actual</p>
          <Button onClick={() => navigate("/")}>Volver al inicio</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header with Timer */}
        <div className="mb-6 flex items-center justify-between bg-white rounded-2xl shadow-lg p-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Examen Celadores SAS</h1>
            <p className="text-slate-600">{answeredCount}/{questions.length} respondidas</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 text-2xl font-bold" data-testid="timer">
              <Clock className="h-6 w-6 text-blue-600" />
              <span className={timeRemaining < 300 ? "text-red-600" : "text-blue-600"}>
                {formatTime(timeRemaining)}
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-1">Pregunta {currentQuestion + 1} de {questions.length}</p>
          </div>
        </div>

        {/* Progress */}
        <div className="mb-6">
          <Progress value={progress} className="h-2" />
        </div>

        {/* Time Warning */}
        {timeRemaining < 300 && timeRemaining > 0 && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              ¡Quedan menos de 5 minutos! Revisa tus respuestas.
            </AlertDescription>
          </Alert>
        )}

        {/* Question Card */}
        <Card className="mb-6 shadow-xl border-0 fade-in">
          <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
            <CardTitle className="text-xl">Pregunta {currentQuestion + 1}</CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <p className="text-lg text-slate-900 mb-6 leading-relaxed">{currentQ.texto}</p>
            
            <RadioGroup 
              value={answers[currentQuestion] !== null ? answers[currentQuestion].toString() : ""} 
              onValueChange={handleAnswerChange}
              data-testid="answer-options"
            >
              <div className="space-y-4">
                {currentQ.opciones.map((opcion, index) => (
                  <div 
                    key={index}
                    className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer hover:border-blue-400 hover:bg-blue-50 ${
                      answers[currentQuestion] === index ? 'border-blue-600 bg-blue-50' : 'border-slate-200'
                    }`}
                    onClick={() => handleAnswerChange(index.toString())}
                  >
                    <RadioGroupItem 
                      value={index.toString()} 
                      id={`option-${index}`}
                      data-testid={`option-${index}`}
                    />
                    <Label 
                      htmlFor={`option-${index}`} 
                      className="flex-1 cursor-pointer text-base"
                    >
                      <span className="font-semibold mr-2">{String.fromCharCode(65 + index)}.</span>
                      {opcion}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex items-center justify-between gap-4">
          <Button
            data-testid="previous-button"
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            variant="outline"
            className="px-6 py-6 rounded-xl"
          >
            <ChevronLeft className="mr-2 h-5 w-5" />
            Anterior
          </Button>

          <div className="flex gap-2 overflow-x-auto px-2">
            {questions.slice(0, 10).map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuestion(index)}
                data-testid={`question-${index + 1}`}
                className={`w-10 h-10 rounded-lg font-semibold transition-all ${
                  currentQuestion === index
                    ? 'bg-blue-600 text-white'
                    : answers[index] !== null
                    ? 'bg-green-100 text-green-700 border-2 border-green-300'
                    : 'bg-slate-100 text-slate-600 border-2 border-slate-200'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          {currentQuestion < questions.length - 1 ? (
            <Button
              data-testid="next-button"
              onClick={() => setCurrentQuestion(Math.min(questions.length - 1, currentQuestion + 1))}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-6 rounded-xl"
            >
              Siguiente
              <ChevronRight className="ml-2 h-5 w-5" />
            </Button>
          ) : (
            <Button
              data-testid="submit-button"
              onClick={handleSubmit}
              disabled={submitting}
              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 px-6 py-6 rounded-xl"
            >
              {submitting ? (
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              ) : (
                <Send className="mr-2 h-5 w-5" />
              )}
              Finalizar
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExamPage;
