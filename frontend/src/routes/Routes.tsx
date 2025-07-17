import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Login from '../pages/Login';
import AuthGuard from '../components/auth/AuthGuard';

export default function AppRoutes() {
  return (
    <Routes>
      <Route 
        path='/dashboard' 
        element={
          <AuthGuard requireAuth={true}>
            <Dashboard />
          </AuthGuard>
        } 
      />
      <Route 
        path='/login' 
        element={
          <AuthGuard requireAuth={false}>
            <Login />
          </AuthGuard>
        } 
      />
      <Route path='/' element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
