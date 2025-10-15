import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Clock, CheckCircle2, Target, BookOpen } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStartExam = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/exam/generate`);
      const exam = response.data;
      navigate(`/exam/${exam.id}`);
    } catch (error) {
      console.error('Error generating exam:', error);
      alert('Error al generar el examen. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12 fade-in">
          <div className="inline-block mb-4">
            <span className="bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-semibold shadow-lg">
              Preparación Oposiciones SAS
            </span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Examen de Celadores
          </h1>
          <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8 leading-relaxed">
            Prepárate para las oposiciones con exámenes tipo test generados por IA
            basados en el temario oficial y la legislación vigente del Servicio Andaluz
            de Salud
          </p>
          <Button
            onClick={handleStartExam}
            disabled={loading}
            data-testid="start-exam-button"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-xl shadow-2xl transform transition hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center gap-3">
                <div className="spinner" />
                <span>Generando examen...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <BookOpen className="w-6 h-6" />
                <span>Comenzar Nuevo Examen</span>
              </div>
            )}
          </Button>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6 mt-16">
          {/* Card 1: Time */}
          <Card className="p-8 bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl hover:shadow-2xl transition-all hover:-translate-y-1 fade-in">
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Clock className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">90 Minutos</h3>
              <p className="text-sm text-gray-600 font-semibold mb-3">Tiempo real de examen oficial</p>
              <p className="text-gray-600 leading-relaxed">
                Simula las condiciones reales del examen con un temporizador de 90
                minutos.
              </p>
            </div>
          </Card>

          {/* Card 2: Questions */}
          <Card className="p-8 bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl hover:shadow-2xl transition-all hover:-translate-y-1 fade-in" style={{animationDelay: '0.1s'}}>
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">50 Preguntas</h3>
              <p className="text-sm text-gray-600 font-semibold mb-3">Test completo tipo oposición</p>
              <p className="text-gray-600 leading-relaxed">
                50 preguntas tipo test con 4 opciones y solo una respuesta correcta.
              </p>
            </div>
          </Card>

          {/* Card 3: Scoring */}
          <Card className="p-8 bg-white/95 backdrop-blur-sm shadow-xl rounded-2xl hover:shadow-2xl transition-all hover:-translate-y-1 fade-in" style={{animationDelay: '0.2s'}}>
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mb-4">
                <Target className="w-8 h-8 text-pink-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Sistema de Puntuación</h3>
              <p className="text-sm text-gray-600 font-semibold mb-3">Puntuación sobre 100 puntos</p>
              <div className="text-left space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-green-600 font-bold">✓</span>
                  <span className="text-gray-700">Correcta: <strong>+2 puntos</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-red-600 font-bold">✗</span>
                  <span className="text-gray-700">Incorrecta: <strong>-0.5 puntos</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 font-bold">○</span>
                  <span className="text-gray-700">En blanco: <strong>0 puntos</strong></span>
                </div>
                <div className="pt-2 border-t border-gray-200 mt-3">
                  <span className="text-purple-600 font-bold">50 correctas = 100 puntos</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Home;