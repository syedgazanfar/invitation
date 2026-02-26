/**
 * Main App Component
 * 
 * This is the root component of the application that sets up:
 * - Material-UI theme
 * - React Router routing
 * - Authentication state management
 * - Route guards for protected and admin routes
 */
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

import { theme } from './theme';
import { useAuthStore } from './store/authStore';

// Layout Components
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import ProtectedRoute from './components/common/ProtectedRoute';
import AdminRoute from './components/common/AdminRoute';
import ErrorBoundary from './components/common/ErrorBoundary';

// Public Pages
import Home from './pages/Home/Home';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import ForgotPassword from './pages/Auth/ForgotPassword';
import Plans from './pages/Plans/Plans';
import Templates from './pages/Plans/Templates';

// Protected Pages
import Dashboard from './pages/Dashboard/Dashboard';
import Orders from './pages/Dashboard/Orders';
import MyInvitations from './pages/Dashboard/MyInvitations';
import Profile from './pages/Dashboard/Profile';
import InvitationBuilder from './pages/InvitationBuilder/Builder';

// Public Invitation Page
import InvitationPage from './pages/Invite/InvitationPage';

// Admin Pages
import AdminDashboard from './pages/Admin/Dashboard';
import AdminOrders from './pages/Admin/Orders';
import AdminUsers from './pages/Admin/Users';
import RealTimeDashboard from './components/admin/RealTimeDashboard';

/**
 * Main App Component
 * 
 * Handles the main application layout, routing, and authentication state.
 */
function App() {
  const { isAuthenticated, loadUser } = useAuthStore();

  // Load user data on app initialization if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadUser().catch(() => {
        // Token invalid, user will be logged out by API interceptor
      });
    }
  }, [isAuthenticated, loadUser]);

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component="main" sx={{ flexGrow: 1 }}>
              <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/plans" element={<Plans />} />
              <Route path="/templates" element={<Templates />} />
              
              {/* Public Invitation Route */}
              <Route path="/invite/:slug" element={<InvitationPage />} />

              {/* Protected Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/dashboard/orders" element={<Orders />} />
                <Route path="/dashboard/invitations" element={<MyInvitations />} />
                <Route path="/dashboard/profile" element={<Profile />} />
                <Route path="/invitation/builder" element={<InvitationBuilder />} />
                <Route path="/invitation/builder/:orderId" element={<InvitationBuilder />} />
              </Route>

              {/* Admin Routes */}
              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<AdminDashboard />} />
                <Route path="/admin/orders" element={<AdminOrders />} />
                <Route path="/admin/users" element={<AdminUsers />} />
                {/* Real-time Dashboard with WebSocket */}
                <Route path="/admin/realtime" element={<RealTimeDashboard />} />
              </Route>

              {/* Catch all */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Box>
            <Footer />
          </Box>
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
