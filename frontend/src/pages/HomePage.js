import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, History, BarChart3, Clock, CheckCircle2, Award } from "lucide-react";

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16 fade-in">
          <div className="inline-block mb-6">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-full text-sm font-semibold shadow-lg">
              Preparación Oposiciones SAS
            </div>
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 mb-6">
            Examen de Celadores
          </h1>
          <p className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto mb-8">
            Prepárate para las oposiciones con exámenes tipo test generados por IA basados en el temario oficial y la legislación vigente del Servicio Andaluz de Salud
          </p>
          <Button
            data-testid="start-exam-button"
            onClick={() => navigate("/exam")}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-6 text-lg rounded-full shadow-xl"
          >
            <BookOpen className="mr-2 h-5 w-5" />
            Comenzar Nuevo Examen
          </Button>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card className="card-hover border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Clock className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle className="text-xl">90 Minutos</CardTitle>
              <CardDescription>Tiempo real de examen oficial</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Simula las condiciones reales del examen con un temporizador de 90 minutos.</p>
            </CardContent>
          </Card>

          <Card className="card-hover border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="h-6 w-6 text-indigo-600" />
              </div>
              <CardTitle className="text-xl">50 Preguntas</CardTitle>
              <CardDescription>Test completo tipo oposición</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">50 preguntas tipo test con 4 opciones y solo una respuesta correcta.</p>
            </CardContent>
          </Card>

          <Card className="card-hover border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Award className="h-6 w-6 text-purple-600" />
              </div>
              <CardTitle className="text-xl">Justificaciones</CardTitle>
              <CardDescription>Aprende de cada pregunta</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600">Cada respuesta incluye justificación basada en temario oficial y legislación.</p>
            </CardContent>
          </Card>
        </div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <Card 
            data-testid="history-card"
            className="card-hover border-0 shadow-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white cursor-pointer"
            onClick={() => navigate("/history")}
          >
            <CardHeader>
              <History className="h-8 w-8 mb-2" />
              <CardTitle className="text-2xl text-white">Historial de Exámenes</CardTitle>
              <CardDescription className="text-blue-100">
                Revisa tus exámenes anteriores y respuestas
              </CardDescription>
            </CardHeader>
          </Card>

          <Card 
            data-testid="stats-card"
            className="card-hover border-0 shadow-lg bg-gradient-to-br from-purple-500 to-pink-600 text-white cursor-pointer"
            onClick={() => navigate("/stats")}
          >
            <CardHeader>
              <BarChart3 className="h-8 w-8 mb-2" />
              <CardTitle className="text-2xl text-white">Estadísticas</CardTitle>
              <CardDescription className="text-purple-100">
                Analiza tu progreso y rendimiento
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
