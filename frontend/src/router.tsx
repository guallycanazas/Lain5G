import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LogsPage } from './pages/LogsPage';
import { MetricsPage } from './pages/MetricsPage';
import { ProfileConfigPage } from './pages/ProfileConfigPage';
import { PreparationPage } from './pages/PreparationPage';
import { RealImsPage } from './pages/RealImsPage';
import { RfSafetyPage } from './pages/RfSafetyPage';
import { RunDetailPage } from './pages/RunDetailPage';
import { RunsPage } from './pages/RunsPage';
import { ScenarioDetailPage } from './pages/ScenarioDetailPage';
import { ScenariosPage } from './pages/ScenariosPage';
import { SubscriberCreatePage } from './pages/SubscriberCreatePage';
import { SubscriberDetailPage } from './pages/SubscriberDetailPage';
import { SubscriberEditPage } from './pages/SubscriberEditPage';
import { SubscribersPage } from './pages/SubscribersPage';
import { SettingsPage } from './pages/SettingsPage';
import { TopologyPage } from './pages/TopologyPage';
import { ValidationPage } from './pages/ValidationPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'validation', element: <ValidationPage /> },
      { path: 'topology', element: <TopologyPage /> },
      { path: 'metrics', element: <MetricsPage /> },
      { path: 'logs', element: <LogsPage /> },
      { path: 'configuration', element: <Navigate to="/deployments" replace /> },
      { path: 'deployments', element: <ProfileConfigPage /> },
      { path: 'preparation', element: <PreparationPage /> },
      { path: 'ims-real', element: <RealImsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'rf-safety', element: <RfSafetyPage /> },
      { path: 'scenarios', element: <ScenariosPage /> },
      { path: 'scenarios/:scenarioId', element: <ScenarioDetailPage /> },
      { path: 'subscribers', element: <SubscribersPage /> },
      { path: 'subscribers/new', element: <SubscriberCreatePage /> },
      { path: 'subscribers/:imsi', element: <SubscriberDetailPage /> },
      { path: 'subscribers/:imsi/edit', element: <SubscriberEditPage /> },
      { path: 'runs', element: <RunsPage /> },
      { path: 'runs/:runId', element: <RunDetailPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
