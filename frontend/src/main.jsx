import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './styles.css';
import ErrorBoundary from './components/ErrorBoundary';
import './api/authSession';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary><App /></ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>
);
