import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

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

  if (loading) return <div className="muted">Đang tải tổng quan...</div>;

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
        <div className="stat-box"><div className="stat-label">Vị trí đang tuyển</div><div className="stat-value">{overview.open_jobs ?? overview.total_jobs}</div><div className="stat-hint">Đang nhận hồ sơ</div></div>
        <div className="stat-box"><div className="stat-label">Ứng viên</div><div className="stat-value">{overview.total_candidates}</div><div className="stat-hint">Hồ sơ đã tiếp nhận</div></div>
        <div className="stat-box"><div className="stat-label">CV đã phân tích</div><div className="stat-value">{overview.cv_analyzed}</div><div className="stat-hint">Phân tích hoàn tất</div></div>
        <div className="stat-box"><div className="stat-label">Điểm phù hợp trung bình</div><div className="stat-value">{Number(overview.average_matching_score || 0).toFixed(1)}%</div><div className="stat-hint">Trên {overview.total_matches} lượt đánh giá</div></div>
      </section>

      <section className="dashboard-panels">
        <div className="card">
          <div className="section-heading"><div><h2>Phân loại phù hợp</h2><p className="muted">Theo kết quả mô hình</p></div><span className="muted">{overview.total_matches} lượt</span></div>
          {['HIGH', 'MEDIUM', 'LOW'].map((label) => {
            const count = Number(distribution[label] || 0);
            const percent = (count / distributionTotal) * 100;
            return <div className="distribution-row" key={label}>
              <div className="list-item-row"><strong>{label}</strong><span>{count} <span className="muted">({percent.toFixed(0)}%)</span></span></div>
              <div className="progress-bar"><div className={`progress-fill progress-${label.toLowerCase()}`} style={{ width: `${percent}%` }} /></div>
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
