import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { DevicesPage } from '../pages/DevicesPage';
import { DeviceDetailPage } from '../pages/DeviceDetailPage';
import { PredictionsPage } from '../pages/PredictionsPage';
import { AlertsPage } from '../pages/AlertsPage';
import { MachineLearningPage } from '../pages/MachineLearningPage';
import { AboutPage } from '../pages/AboutPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'devices', element: <DevicesPage /> },
      { path: 'devices/:id', element: <DeviceDetailPage /> },
      { path: 'predictions', element: <PredictionsPage /> },
      { path: 'alerts', element: <AlertsPage /> },
      { path: 'ml', element: <MachineLearningPage /> },
      { path: 'about', element: <AboutPage /> },
    ],
  },
]);
