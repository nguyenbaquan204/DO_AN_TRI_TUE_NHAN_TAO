import { Routes, Route, Navigate, Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
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

import ExperimentsPage from './pages/ExperimentsPage';

const navigation = [
  { key: 'experiments', label: 'Đánh giá mô hình', href: '/experiments', icon: 'dashboard' },
  { key: 'dashboard', label: 'Tổng quan', href: '/dashboard', icon: 'dashboard' },
  { key: 'jobs', label: 'Vị trí tuyển dụng', href: '/jobs', icon: 'briefcase' },
  { key: 'upload-cv', label: 'Tải hồ sơ CV', href: '/upload-cv', icon: 'upload' },
  { key: 'candidates', label: 'Ứng viên', href: '/candidates', icon: 'users' },
];

function Icon({ name, size = 20 }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' };
  const shapes = {
    dashboard: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="5" rx="1.5" /><rect x="13.5" y="11.5" width="7" height="9" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /></>,
    briefcase: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7M3 12h18M10 12v2h4v-2" /></>,
    upload: <><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" /></>,
    users: <><path d="M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20" /><circle cx="10" cy="8" r="3.5" /><path d="M16 4.7a3.5 3.5 0 0 1 0 6.6M20 20v-1.5a3.5 3.5 0 0 0-2.6-3.4" /></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3" /><path d="M12 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5" /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...common}>{shapes[name] || shapes.dashboard}</svg>;
}

function getPageTitle(pathname, activeItem) {
  if (pathname === '/jobs/create') return 'Tạo vị trí tuyển dụng';
  if (/\/jobs\/[^/]+\/edit$/.test(pathname)) return 'Chỉnh sửa vị trí tuyển dụng';
  if (/\/jobs\/[^/]+\/candidates/.test(pathname) || /\/jobs\/[^/]+\/ranking$/.test(pathname)) return 'Xếp hạng ứng viên';
  if (/\/jobs\/[^/]+\/upload-candidates$/.test(pathname)) return 'Tải CV cho vị trí';
  if (/\/jobs\/[^/]+$/.test(pathname)) return 'Chi tiết vị trí tuyển dụng';
  if (/\/candidates\/[^/]+$/.test(pathname)) return 'Hồ sơ ứng viên';
  if (/\/matching\/[^/]+$/.test(pathname)) return 'Chi tiết đánh giá phù hợp';
  return activeItem?.label || 'Tổng quan';
}

function App() {
  const isAuthenticated = Boolean(localStorage.getItem('token'));
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = location.pathname.startsWith('/jobs')
    ? (location.pathname.includes('upload-candidates') ? 'upload-cv' : 'jobs')
    : location.pathname.startsWith('/candidates') ? 'candidates'
      : location.pathname.startsWith('/experiments') ? 'experiments'
      : location.pathname.startsWith('/upload-cv') ? 'upload-cv' : 'dashboard';
  const activeItem = navigation.find((item) => item.key === selectedKey);

  const signOut = () => {
    localStorage.removeItem('token');
    navigate('/login', { replace: true });
  };

  return (
    <div className={isAuthenticated ? 'app-shell' : 'auth-shell'}>
      {isAuthenticated ? <>
        <aside className="app-sidebar">
          <Link to="/dashboard" className="brand-lockup" aria-label="AI Recruit, về tổng quan">
            <span className="brand-mark">A</span>
            <span className="brand-copy"><strong>AI Recruit</strong><small>TRỢ LÝ TUYỂN DỤNG</small></span>
          </Link>
          <div className="nav-caption">KHÔNG GIAN LÀM VIỆC</div>
          <nav className="app-navigation" aria-label="Điều hướng chính">
            {navigation.map((item) => <NavLink
              key={item.key}
              to={item.href}
              end={item.key === 'dashboard' || item.key === 'upload-cv'}
              className={() => `nav-item ${selectedKey === item.key ? 'nav-item-active' : ''}`}
              aria-current={selectedKey === item.key ? 'page' : undefined}
            >
              <span className="nav-icon"><Icon name={item.icon} /></span><span>{item.label}</span>
              {selectedKey === item.key ? <span className="nav-indicator" aria-hidden="true" /> : null}
            </NavLink>)}
          </nav>
          <div className="sidebar-spacer" />
          <div className="sidebar-note"><span className="online-dot" /><span><strong>Hệ thống sẵn sàng</strong><small>Không gian tuyển dụng</small></span></div>
        </aside>
        <div className="app-main">
          <header className="app-header">
            <div className="header-title-group">
              <span className="header-kicker">AI RECRUIT <span aria-hidden="true">/</span> {activeItem?.label?.toUpperCase() || 'TỔNG QUAN'}</span>
              <strong>{getPageTitle(location.pathname, activeItem)}</strong>
            </div>
            <div className="header-actions">
              <div className="header-profile" aria-label="Không gian nhà tuyển dụng">
                <span className="profile-avatar">N</span>
                <span className="profile-copy"><strong>Nhà tuyển dụng</strong><small>Không gian làm việc</small></span>
              </div>
              <button className="ghost-button logout-button" type="button" onClick={signOut}>
                <Icon name="logout" size={17} /><span>Đăng xuất</span>
              </button>
            </div>
          </header>
          <main className="app-content">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/experiments" element={<ExperimentsPage />} />
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
