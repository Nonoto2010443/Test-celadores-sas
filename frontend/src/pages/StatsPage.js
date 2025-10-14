import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Home, TrendingUp, Target, Award, Clock } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = BACKEND_URL; // .env already includes /api

const StatsPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/exams/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} seg`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Cargando estadísticas...</p>
      </div>
    );
  }

  if (!stats || stats.total_examenes === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          <Button
            onClick={() => navigate("/")}
            variant="ghost"
            className="mb-4"
          >
            <Home className="mr-2 h-4 w-4" />
            Volver al Inicio
          </Button>
          <Card className="border-0 shadow-lg">
            <CardContent className="p-12 text-center">
              <p className="text-slate-600 mb-4">No hay estadísticas disponibles todavía.</p>
              <Button
                onClick={() => navigate("/exam")}
                className="bg-gradient-to-r from-blue-600 to-indigo-600"
              >
                Realizar Primer Examen
              </Button>
            </CardContent>
          </Card>
        </div>
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
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-4">Estadísticas</h1>
          <p className="text-slate-600">Analiza tu progreso con el sistema de puntuación oficial</p>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
            <CardHeader>
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mb-2">
                <Target className="h-6 w-6" />
              </div>
              <CardTitle className="text-white">Total Exámenes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold" data-testid="total-exams">{stats.total_examenes}</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
            <CardHeader>
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mb-2">
                <Award className="h-6 w-6" />
              </div>
              <CardTitle className="text-white">Mejor Puntuación</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold" data-testid="best-score">{stats.mejor_sobre_100.toFixed(2)}</div>
              <div className="text-lg opacity-90 mt-2">sobre 100 pts</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-pink-600 text-white">
            <CardHeader>
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mb-2">
                <TrendingUp className="h-6 w-6" />
              </div>
              <CardTitle className="text-white">Promedio</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold" data-testid="avg-score">{stats.promedio_sobre_100.toFixed(2)}</div>
              <div className="text-lg opacity-90 mt-2">sobre 100 pts</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-500 to-red-600 text-white">
            <CardHeader>
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mb-2">
                <Clock className="h-6 w-6" />
              </div>
              <CardTitle className="text-white">Tiempo Promedio</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold" data-testid="avg-time">{formatTime(stats.tiempo_promedio)}</div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Stats */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Progreso de Puntuaciones</CardTitle>
              <CardDescription>Sistema oficial SAS: Correctas (+2 pts) - Incorrectas (-0.5 pts)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-semibold">Mejor Puntuación</span>
                  <span className="text-green-600 font-bold">{stats.mejor_sobre_100.toFixed(2)} pts</span>
                </div>
                <Progress value={stats.mejor_sobre_100} className="h-3" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-semibold">Puntuación Promedio</span>
                  <span className="text-blue-600 font-bold">{stats.promedio_sobre_100.toFixed(2)} pts</span>
                </div>
                <Progress value={stats.promedio_sobre_100} className="h-3" />
              </div>

              {stats.ultima_sobre_100 !== null && (
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-semibold">Última Puntuación</span>
                    <span className="text-purple-600 font-bold">{stats.ultima_sobre_100.toFixed(2)} pts</span>
                  </div>
                  <Progress value={stats.ultima_sobre_100} className="h-3" />
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Análisis de Rendimiento</CardTitle>
              <CardDescription>Insights sobre tu preparación</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {stats.promedio_sobre_100 >= 80 && (
                <div className="p-4 bg-green-50 border-l-4 border-green-600 rounded">
                  <p className="font-semibold text-green-900 mb-1">¡Excelente preparación!</p>
                  <p className="text-sm text-green-800">Tu promedio está por encima de 80 puntos. Mantén este ritmo.</p>
                </div>
              )}
              {stats.promedio_sobre_100 >= 60 && stats.promedio_sobre_100 < 80 && (
                <div className="p-4 bg-blue-50 border-l-4 border-blue-600 rounded">
                  <p className="font-semibold text-blue-900 mb-1">Buen progreso</p>
                  <p className="text-sm text-blue-800">Estás en el camino correcto. Sigue practicando para mejorar.</p>
                </div>
              )}
              {stats.promedio_sobre_100 < 60 && (
                <div className="p-4 bg-yellow-50 border-l-4 border-yellow-600 rounded">
                  <p className="font-semibold text-yellow-900 mb-1">Necesitas más práctica</p>
                  <p className="text-sm text-yellow-800">Repasa el temario y realiza más exámenes para mejorar.</p>
                </div>
              )}

              <div className="p-4 bg-slate-50 border-l-4 border-slate-600 rounded">
                <p className="font-semibold text-slate-900 mb-1">Sistema de Puntuación</p>
                <p className="text-sm text-slate-800">
                  Correctas (+2 pts) - Incorrectas (-0.5 pts) - En blanco (0 pts)
                </p>
              </div>

              <div className="p-4 bg-indigo-50 border-l-4 border-indigo-600 rounded">
                <p className="font-semibold text-indigo-900 mb-1">Recomendación</p>
                <p className="text-sm text-indigo-800">
                  Revisa tus exámenes anteriores para identificar áreas de mejora y fortalece los temas donde tengas más errores.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Button */}
        <div className="mt-8 text-center">
          <Button
            onClick={() => navigate("/exam")}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6 text-lg rounded-full shadow-xl"
            data-testid="new-exam-button"
          >
            Realizar Nuevo Examen
          </Button>
        </div>
      </div>
    </div>
  );
};

export default StatsPage;
