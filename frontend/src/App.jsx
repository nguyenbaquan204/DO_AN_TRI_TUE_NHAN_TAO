import { Routes, Route, Navigate, Link, useLocation, useNavigate } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import JobCandidatesPage from './pages/JobCandidatesPage';
import UploadCvPage from './pages/UploadCvPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CandidatesPage from './pages/CandidatesPage';
import CandidateDetailPage from './pages/CandidateDetailPage';
import MatchingDetailPage from './pages/MatchingDetailPage';

const navigation = [
  { key: 'dashboard', label: 'Tổng quan', href: '/dashboard', icon: '◫' },
  { key: 'jobs', label: 'Vị trí tuyển dụng', href: '/jobs', icon: '▤' },
  { key: 'upload-cv', label: 'Tải hồ sơ CV', href: '/upload-cv', icon: '↑' },
  { key: 'candidates', label: 'Ứng viên', href: '/candidates', icon: '◎' },
];

function App() {
  const isAuthenticated = Boolean(localStorage.getItem('token'));
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = location.pathname.startsWith('/jobs') ? 'jobs'
    : location.pathname.startsWith('/candidates') ? 'candidates'
      : location.pathname.startsWith('/upload-cv') ? 'upload-cv' : 'dashboard';

  return (
    <div className={isAuthenticated ? 'app-shell' : 'auth-shell'}>
      {isAuthenticated ? <>
        <aside className="app-sidebar">
          <Link to="/dashboard" className="brand-lockup"><span className="brand-mark">A</span><span><strong>AI Recruit</strong><small>TRỢ LÝ TUYỂN DỤNG</small></span></Link>
          <div className="nav-caption">KHÔNG GIAN LÀM VIỆC</div>
          <nav className="app-navigation" aria-label="Điều hướng chính">
            {navigation.map((item) => <button key={item.key} type="button" className={`nav-item ${selectedKey === item.key ? 'nav-item-active' : ''}`} onClick={() => navigate(item.href)}><span className="nav-icon" aria-hidden="true">{item.icon}</span>{item.label}</button>)}
          </nav>
          <div className="sidebar-note"><span className="online-dot" />Hệ thống sẵn sàng</div>
        </aside>
        <div className="app-main">
          <header className="app-header"><div><span className="header-kicker">BẢNG ĐIỀU KHIỂN</span><strong>Không gian nhà tuyển dụng</strong></div><button className="ghost-button" onClick={() => { localStorage.removeItem('token'); navigate('/login', { replace: true }); }}>Đăng xuất</button></header>
          <main className="app-content">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/upload-cv" element={<UploadCvPage />} />
              <Route path="/jobs/:jobId/upload-candidates" element={<UploadCvPage />} />
              <Route path="/jobs/create" element={<JobsPage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/jobs/:jobId/edit" element={<JobsPage />} />
              <Route path="/jobs/:jobId" element={<JobDetailPage />} />
              <Route path="/jobs/:jobId/candidates" element={<JobCandidatesPage />} />
              <Route path="/jobs/:jobId/candidates/:candidateId" element={<CandidateDetailPage />} />
              <Route path="/jobs/:jobId/ranking" element={<JobCandidatesPage />} />
              <Route path="/matching/:matchId" element={<MatchingDetailPage />} />
              <Route path="/candidates" element={<CandidatesPage />} />
              <Route path="/candidates/:id" element={<CandidateDetailPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </> : <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>}
    </div>
  );
}

export default App;
