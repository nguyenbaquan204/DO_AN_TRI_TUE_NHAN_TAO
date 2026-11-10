import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const initialOverview = {
  total_jobs: 0,
  total_candidates: 0,
  cv_analyzed: 0,
  total_matches: 0,
  average_matching_score: 0,
  suitability_distribution: {},
  candidates_per_job: [],
  cv_processing_status: {},
};

export default function DashboardPage() {
  const [overview, setOverview] = useState(initialOverview);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      try {
        const [overviewRes, jobsRes] = await Promise.all([
          axios.get(`${API_URL}/api/dashboard/overview`, { headers }),
          axios.get(`${API_URL}/api/jobs`, { headers }),
        ]);
        setOverview({ ...initialOverview, ...overviewRes.data });
        setJobs((jobsRes.data || []).filter((job) => job.status === 'open').slice(0, 5));
      } catch (err) {
        setError(err.response?.data?.detail || 'Không thể tải dữ liệu tổng quan.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) return <LoadingState label="Đang tải số liệu tổng quan..." />;

  const distribution = overview.suitability_distribution || {};
  const distributionTotal = Math.max(1, Object.values(distribution).reduce((sum, value) => sum + Number(value || 0), 0));

  return (
    <div className="dashboard-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">KHÔNG GIAN TUYỂN DỤNG</div>
          <h1 className="page-title">Tổng quan</h1>
          <p className="muted">Theo dõi vị trí tuyển dụng, hồ sơ và kết quả sàng lọc.</p>
        </div>
        <Link className="primary-button" to="/jobs/create">+ Tạo vị trí tuyển dụng</Link>
      </div>
      {error ? <div className="error-box">{error}</div> : null}

      <section className="stats-grid" aria-label="Chỉ số tổng quan">
        <div className="stat-box"><div className="stat-topline"><div className="stat-label">Vị trí đang tuyển</div><span className="stat-icon stat-icon-blue" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3.5" y="7" width="17" height="13" rx="2"/><path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7M3.5 12h17"/></svg></span></div><div className="stat-value">{overview.open_jobs ?? overview.total_jobs}</div><div className="stat-hint">Đang nhận hồ sơ</div></div>
        <div className="stat-box"><div className="stat-topline"><div className="stat-label">Ứng viên</div><span className="stat-icon stat-icon-violet" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.3"/><path d="M3 20v-1.3A3.7 3.7 0 0 1 6.7 15h4.6a3.7 3.7 0 0 1 3.7 3.7V20M16 5.2a3.2 3.2 0 0 1 0 5.7M17 15.3a3.7 3.7 0 0 1 4 3.7V20"/></svg></span></div><div className="stat-value">{overview.total_candidates}</div><div className="stat-hint">Hồ sơ đã tiếp nhận</div></div>
        <div className="stat-box"><div className="stat-topline"><div className="stat-label">CV đã phân tích</div><span className="stat-icon stat-icon-green" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 3.5h8l4 4V20a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 20V3.5Z"/><path d="M14 3.5V8h4M9 12h6M9 15.5h6"/></svg></span></div><div className="stat-value">{overview.cv_analyzed}</div><div className="stat-hint">Phân tích hoàn tất</div></div>
        <div className="stat-box"><div className="stat-topline"><div className="stat-label">Điểm phù hợp trung bình</div><span className="stat-icon stat-icon-amber" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 19.5V12m5.3 7.5V5m5.4 14.5v-9m5.3 9V8"/><path d="m3.5 8 5-4 5.2 4.5 6.8-5"/></svg></span></div><div className="stat-value">{Number(overview.average_matching_score || 0).toFixed(1)}%</div><div className="stat-hint">Trên {overview.total_matches} lượt đánh giá</div></div>
      </section>

      <section className="dashboard-panels">
        <div className="card">
          <div className="section-heading"><div><h2>Phân loại phù hợp</h2><p className="muted">Tổng hợp các mức phù hợp đã ghi nhận</p></div><span className="muted">{overview.total_matches} lượt</span></div>
          {['HIGH', 'MEDIUM', 'LOW'].map((label) => {
            const count = Number(distribution[label] || 0);
            const percent = (count / distributionTotal) * 100;
            const displayLabel = label === 'HIGH' ? 'Phù hợp cao' : label === 'MEDIUM' ? 'Phù hợp trung bình' : 'Phù hợp thấp';
            return <div className="distribution-row" key={label}>
              <div className="list-item-row"><strong>{displayLabel}</strong><span>{count} <span className="muted">({percent.toFixed(0)}%)</span></span></div>
              <div className="progress-bar" role="progressbar" aria-label={displayLabel} aria-valuenow={Math.round(percent)} aria-valuemin="0" aria-valuemax="100"><div className={`progress-fill progress-${label.toLowerCase()}`} style={{ width: `${percent}%` }} /></div>
            </div>;
          })}
        </div>
        <div className="card">
          <div className="section-heading"><div><h2>Trạng thái xử lý CV</h2><p className="muted">Tiến độ phân tích hồ sơ</p></div></div>
          {Object.entries(overview.cv_processing_status || {}).map(([status, count]) => (
            <div className="list-item-row" key={status}><span>{status === 'COMPLETED' ? 'Hoàn tất' : status === 'FAILED' ? 'Thất bại' : status === 'PROCESSING' ? 'Đang xử lý' : 'Chờ xử lý'}</span><strong>{count}</strong></div>
          ))}
          {!Object.values(overview.cv_processing_status || {}).some(Number) ? <p className="muted">Chưa có hồ sơ được xử lý.</p> : null}
          <Link className="text-link" to="/upload-cv">Tải CV lên →</Link>
        </div>
      </section>

      <section className="card">
        <div className="section-heading"><div><h2>Vị trí gần đây</h2><p className="muted">Mở vị trí để xem hồ sơ và kết quả sàng lọc.</p></div><Link className="text-link" to="/jobs">Tất cả vị trí →</Link></div>
        {jobs.length ? <div className="stack">
          {jobs.map((job) => {
            const count = (overview.candidates_per_job || []).find((item) => Number(item.job_id) === Number(job.id))?.count || 0;
            return <div className="list-item-row dashboard-job" key={job.id}>
              <div><Link className="job-title-link" to={`/jobs/${job.id}`}>{job.title}</Link><div className="muted">{job.department || 'Chưa phân loại'} · {job.location || 'Chưa có địa điểm'}</div></div>
              <div className="row-actions"><span className="muted">{count} lượt đánh giá</span><span className={`status-badge ${job.status === 'open' ? 'status-open' : ''}`}>{job.status === 'open' ? 'Đang mở' : 'Đã đóng'}</span><Link to={`/jobs/${job.id}/candidates`}>Xếp hạng</Link></div>
            </div>;
          })}
        </div> : <div className="empty-state"><strong>Chưa có vị trí tuyển dụng</strong><p className="muted">Tạo vị trí đầu tiên để bắt đầu tiếp nhận và sàng lọc ứng viên.</p><Link className="primary-button" to="/jobs/create">Tạo vị trí tuyển dụng</Link></div>}
      </section>
    </div>
  );
}
