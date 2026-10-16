import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function JobCandidatesPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ suitability: '', min_confidence: '', search: '' });

  useEffect(() => {
    const loadData = async () => {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      try {
        const [jobRes, matchesRes] = await Promise.all([
          axios.get(`${API_URL}/api/jobs/${jobId}`, { headers }),
          axios.get(`${API_URL}/api/matching/jobs/${jobId}/matches`, { headers, params: Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== '')) }),
        ]);
        setJob(jobRes.data);
        setMatches(matchesRes.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load ranking');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [jobId, filters]);

  if (loading) return <div>Đang tải xếp hạng...</div>;
  if (!job) return <div className="error-box">{error || 'Job not found'}</div>;

  return (
    <div>
      <div className="page-title">Xếp hạng ứng viên - {job.title}</div>
      <p className="muted">Thứ hạng dựa trên kỹ năng, kinh nghiệm, học vấn và nội dung hồ sơ. Nhãn mô hình chỉ là thông tin tham khảo.</p>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="page-actions" style={{ marginBottom: 16 }}>
        <Link className="ghost-button" to={`/jobs/${jobId}`}>Quay lại vị trí</Link>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="form-row">
          <input className="input" placeholder="Tìm ứng viên" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
          <select className="select" value={filters.suitability} onChange={(event) => setFilters({ ...filters, suitability: event.target.value })}>
            <option value="">Tất cả mức độ phù hợp</option><option value="HIGH">Phù hợp cao (HIGH)</option><option value="MEDIUM">Phù hợp trung bình (MEDIUM)</option><option value="LOW">Phù hợp thấp (LOW)</option>
          </select>
          <input className="input" type="number" min="0" max="1" step="0.05" placeholder="Độ tin cậy tối thiểu (0-1)" value={filters.min_confidence} onChange={(event) => setFilters({ ...filters, min_confidence: event.target.value })} />
        </div>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Hạng</th><th>Ứng viên</th><th>Điểm phù hợp</th><th>Nhãn mô hình</th><th>Độ tin cậy</th><th>Kỹ năng</th><th>Thao tác</th></tr>
            </thead>
            <tbody>
              {matches.length ? matches.map((match, index) => (
                <tr key={match.id}>
                  <td>#{index + 1}</td>
                  <td><Link to={`/candidates/${match.candidate_id}`}>{match.candidate_name}</Link></td>
                  <td><span className="badge">{Number(match.overall_score || 0).toFixed(1)}%</span></td>
                  <td><span className="badge">{match.predicted_class || 'FALLBACK'}</span></td>
                  <td>{match.model_confidence == null ? 'Rule-based fallback' : `${(Number(match.model_confidence) * 100).toFixed(1)}%`}</td>
                  <td>{Number(match.skill_score || 0).toFixed(1)}%</td>
                  <td><Link to={`/matching/${match.id}`}>Chi tiết</Link></td>
                </tr>
              )) : (
                <tr><td colSpan="7" className="muted">Chưa có ứng viên được đánh giá.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
