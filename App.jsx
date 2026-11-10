import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';

// Patient Suite
import PatientDashboard from './pages/patient/PatientDashboard';
import VitalsMonitor from './pages/patient/VitalsMonitor';
import AIHealthInsights from './pages/patient/AIHealthInsights';
import MedicalReports from './pages/patient/MedicalReports';
import BookAppointment from './pages/patient/BookAppointment';
import PatientConsultations from './pages/patient/PatientConsultations';
import WellnessRewards from './pages/patient/WellnessRewards';
import HealthProfile from './pages/patient/HealthProfile';
import Leaderboard from './pages/Leaderboard';

// Doctor Suite
import DoctorDashboard from './pages/doctor/DoctorDashboard';
import DoctorAppointments from './pages/doctor/DoctorAppointments';
import ConsultationRoom from './pages/doctor/ConsultationRoom';
import PatientList from './pages/doctor/PatientList';
import DoctorProfile from './pages/doctor/DoctorProfile';

// Admin Suite
import AdminDashboard from './pages/admin/AdminDashboard';
import UserManagement from './pages/admin/UserManagement';
import DoctorVerification from './pages/admin/DoctorVerification';
import SystemLogs from './pages/admin/SystemLogs';

function AppContent() {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState('home');
  const [activeApptForConsult, setActiveApptForConsult] = useState(null);

  // Sync default tab when user logs in or switches role
  useEffect(() => {
    if (user) {
      if (user.role === 'doctor') {
        setCurrentTab('doctor-dashboard');
      } else if (user.role === 'admin') {
        setCurrentTab('admin-dashboard');
      } else {
        setCurrentTab('patient-dashboard');
      }
    } else {
      if (currentTab !== 'login' && currentTab !== 'register') {
        setCurrentTab('home');
      }
    }
  }, [user?.role, user?._id]);

  const handleNavigate = (tab) => {
    setCurrentTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderContent = () => {
    if (!user) {
      if (currentTab === 'login') return <Login onNavigate={handleNavigate} />;
      if (currentTab === 'register') return <Register onNavigate={handleNavigate} />;
      return <Home onNavigate={handleNavigate} />;
    }

    // Patient Routes
    if (user.role === 'patient') {
      switch (currentTab) {
        case 'patient-dashboard':
          return <PatientDashboard onNavigate={handleNavigate} />;
        case 'vitals-monitor':
          return <VitalsMonitor />;
        case 'ai-insights':
          return <AIHealthInsights />;
        case 'medical-reports':
          return <MedicalReports />;
        case 'book-appointment':
          return <BookAppointment onNavigate={handleNavigate} />;
        case 'consultations':
          return <PatientConsultations />;
        case 'wellness':
          return <WellnessRewards />;
        case 'leaderboard':
          return <Leaderboard onNavigate={handleNavigate} />;
        case 'health-profile':
          return <HealthProfile />;
        default:
          return <PatientDashboard onNavigate={handleNavigate} />;
      }
    }

    // Doctor Routes
    if (user.role === 'doctor') {
      switch (currentTab) {
        case 'doctor-dashboard':
          return (
            <DoctorDashboard
              onNavigate={handleNavigate}
              onStartConsultation={(appt) => {
                setActiveApptForConsult(appt);
                setCurrentTab('consultation-room');
              }}
            />
          );
        case 'doctor-appointments':
          return (
            <DoctorAppointments
              onNavigate={handleNavigate}
              onStartConsultation={(appt) => {
                setActiveApptForConsult(appt);
                setCurrentTab('consultation-room');
              }}
            />
          );
        case 'consultation-room':
          return (
            <ConsultationRoom
              activeAppointment={activeApptForConsult}
              onNavigate={handleNavigate}
            />
          );
        case 'patient-list':
          return (
            <PatientList
              onNavigate={handleNavigate}
              onStartConsultation={(appt) => {
                setActiveApptForConsult(appt);
                setCurrentTab('consultation-room');
              }}
            />
          );
        case 'doctor-profile':
          return <DoctorProfile />;
        default:
          return (
            <DoctorDashboard
              onNavigate={handleNavigate}
              onStartConsultation={(appt) => {
                setActiveApptForConsult(appt);
                setCurrentTab('consultation-room');
              }}
            />
          );
      }
    }

    // Admin Routes
    if (user.role === 'admin') {
      switch (currentTab) {
        case 'admin-dashboard':
          return <AdminDashboard onNavigate={handleNavigate} />;
        case 'user-management':
          return <UserManagement />;
        case 'doctor-verification':
          return <DoctorVerification />;
        case 'system-logs':
          return <SystemLogs />;
        case 'leaderboard':
          return <Leaderboard onNavigate={handleNavigate} />;
        default:
          return <AdminDashboard onNavigate={handleNavigate} />;
      }
    }

    return <Home onNavigate={handleNavigate} />;
  };

  return (
    <div className="app-container">
      {user && (
        <Sidebar
          currentTab={currentTab}
          onSelectTab={handleNavigate}
        />
      )}

      <div className="main-content">
        <Navbar
          onNavigate={handleNavigate}
          activeTab={currentTab}
        />
        <main className="page-wrapper">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}
