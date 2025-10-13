import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Home, Calendar, Clock, Award, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HistoryPage = () => {
  const navigate = useNavigate();
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/exams/history`);
      setExams(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} seg`;
  };

  const getScoreColor = (score) => {
    const percentage = (score / 50) * 100;
    if (percentage >= 80) return "text-green-600";
    if (percentage >= 60) return "text-blue-600";
    if (percentage >= 40) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score) => {
    const percentage = (score / 50) * 100;
    if (percentage >= 80) return "bg-green-100 border-green-300";
    if (percentage >= 60) return "bg-blue-100 border-blue-300";
    if (percentage >= 40) return "bg-yellow-100 border-yellow-300";
    return "bg-red-100 border-red-300";
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Cargando historial...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => navigate("/")}
            variant="ghost"
            className="mb-4"
            data-testid="back-home-button"
          >
            <Home className="mr-2 h-4 w-4" />
            Volver al Inicio
          </Button>
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-4">Historial de Exámenes</h1>
          <p className="text-slate-600">Revisa todos tus exámenes anteriores y tu progreso</p>
        </div>

        {exams.length === 0 ? (
          <Card className="border-0 shadow-lg">
            <CardContent className="p-12 text-center">
              <p className="text-slate-600 mb-4">No has realizado ningún examen todavía.</p>
              <Button
                onClick={() => navigate("/exam")}
                className="bg-gradient-to-r from-blue-600 to-indigo-600"
              >
                Comenzar Primer Examen
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {exams.map((exam, index) => {
              const percentage = (exam.puntuacion / 50) * 100;
              const fecha = new Date(exam.fecha);

              return (
                <Card 
                  key={exam.id} 
                  className="border-0 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                  onClick={() => navigate(`/results/${exam.id}`)}
                  data-testid={`exam-${index}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between gap-6">
                      <div className="flex items-center gap-6 flex-1">
                        <div className={`w-20 h-20 rounded-2xl border-2 ${getScoreBg(exam.puntuacion)} flex items-center justify-center flex-shrink-0`}>
                          <div className="text-center">
                            <div className={`text-2xl font-bold ${getScoreColor(exam.puntuacion)}`}>
                              {exam.puntuacion}
                            </div>
                            <div className="text-xs text-slate-600">/ 50</div>
                          </div>
                        </div>

                        <div className="flex-1">
                          <h3 className="font-bold text-lg text-slate-900 mb-2">
                            Examen #{exams.length - index}
                          </h3>
                          <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              <span>{format(fecha, "d 'de' MMMM, yyyy", { locale: es })}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              <span>{formatTime(exam.tiempo_usado)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Award className="h-4 w-4" />
                              <span className={getScoreColor(exam.puntuacion)}>
                                {percentage.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <ChevronRight className="h-6 w-6 text-slate-400" />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
