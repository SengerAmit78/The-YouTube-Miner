import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/index';
import RunForm from './pages/run';
import ResultsView from './pages/results/ResultsViewNew';
const App: React.FC = () => (
  <Router>
    <Routes>
      <Route path="/" element={<Navigate to="/run" replace />} />
      <Route path="/run" element={<RunForm />} />
      <Route path="/results/:runId" element={<ResultsView />} />
      <Route path="/landing" element={<Landing />} />
    </Routes>
  </Router>
);

export default App;
