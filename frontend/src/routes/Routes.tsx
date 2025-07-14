import { Routes, Route } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Login from '../pages/Login';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path='/dashboard' element={<Dashboard />} />
      <Route path='/login' element={<Login />} />
      <Route path='/' element={<Login />} />
    </Routes>
  );
}
