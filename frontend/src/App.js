import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import '@/App.css';
import Home from '@/pages/Home';
import ExamPage from '@/pages/ExamPage';
import ResultsPage from '@/pages/ResultsPage';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/exam/:examId" element={<ExamPage />} />
          <Route path="/results/:resultId" element={<ResultsPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;