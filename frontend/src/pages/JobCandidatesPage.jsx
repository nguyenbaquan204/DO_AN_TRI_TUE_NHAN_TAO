import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';
import RecruitmentWorkspace from '../components/RecruitmentWorkspace';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function JobCandidatesPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [screening, setScreening] = useState(false);
  const [screeningMessage, setScreeningMessage] = useState('');
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

  const screenSavedCandidates = async () => {
    setScreening(true);
    setError('');
    setScreeningMessage('');
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const candidatesResponse = await axios.get(`${API_URL}/api/candidates`, { headers });
      const candidateIds = (candidatesResponse.data || [])
        .filter((candidate) => candidate.analysis_status === 'COMPLETED')
        .map((candidate) => candidate.id);
      if (!candidateIds.length) {
        setScreeningMessage('Chưa có hồ sơ CV đã phân tích. Hãy tải CV lên trước khi chạy xếp hạng.');
        return;
      }

      let completed = 0;
      let failed = 0;
      for (let index = 0; index < candidateIds.length; index += 100) {
        const batchResponse = await axios.post(
          `${API_URL}/api/matching/jobs/${jobId}/screen-batch`,
          { candidate_ids: candidateIds.slice(index, index + 100) },
          { headers },
        );
        completed += batchResponse.data?.completed || 0;
        failed += batchResponse.data?.failed || 0;
      }
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ''));
      const matchesResponse = await axios.get(`${API_URL}/api/matching/jobs/${jobId}/matches`, { headers, params });
      setMatches(matchesResponse.data || []);
      setScreeningMessage(`Đã chấm ${completed} hồ sơ CV${failed ? `, ${failed} hồ sơ gặp lỗi` : ''}. Thứ hạng đã được cập nhật.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể chấm các hồ sơ CV đã lưu.');
    } finally {
      setScreening(false);
    }
  };

  if (loading) return <LoadingState label="Đang tải bảng xếp hạng..." />;
  if (!job) return <div className="error-box">{error || 'Job not found'}</div>;

  return (
    <div className="ranking-page">
      <div className="page-heading">
        <div><div className="eyebrow">KẾT QUẢ SÀNG LỌC</div><h1 className="page-title">Xếp hạng ứng viên</h1><p className="muted">{job.title} · {matches.length} hồ sơ đã đánh giá</p></div>
        <div className="page-actions">
          <Link className="ghost-button" to={`/jobs/${jobId}`}>Chi tiết vị trí</Link>
          <Link className="ghost-button" to={`/jobs/${jobId}/upload-candidates`}>+ Tải CV</Link>
          <button className="primary-button" type="button" onClick={screenSavedCandidates} disabled={screening}>{screening ? <><span className="button-spinner" aria-hidden="true" />Đang chấm hồ sơ...</> : 'Chấm tất cả CV đã lưu'}</button>
        </div>
      </div>
      <RecruitmentWorkspace jobId={jobId} matches={matches} />
      {error ? <div className="error-box">{error}</div> : null}
      {screeningMessage ? <div className="success-box" role="status">{screeningMessage}</div> : null}
      <div className="card filter-panel">
        <div className="filter-panel-heading"><strong>Lọc danh sách</strong><span className="muted">Điểm số hỗ trợ tham khảo; hãy xem bằng chứng trong từng hồ sơ.</span></div>
        <div className="form-row">
          <input className="input" aria-label="Tìm ứng viên" placeholder="Tìm theo tên ứng viên..." value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
          <select className="select" value={filters.suitability} onChange={(event) => setFilters({ ...filters, suitability: event.target.value })}>
            <option value="">Tất cả mức độ phù hợp</option><option value="HIGH">Phù hợp cao (HIGH)</option><option value="MEDIUM">Phù hợp trung bình (MEDIUM)</option><option value="LOW">Phù hợp thấp (LOW)</option>
          </select>
          <input className="input" type="number" min="0" max="1" step="0.05" aria-label="Độ tin cậy mô hình tối thiểu" placeholder="Độ tin cậy tối thiểu (0–1)" value={filters.min_confidence} onChange={(event) => setFilters({ ...filters, min_confidence: event.target.value })} />
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
                  <td><span className={`rank-number ${index < 3 ? `rank-number-${index + 1}` : ''}`}>{String(index + 1).padStart(2, '0')}</span></td>
                  <td><Link to={`/candidates/${match.candidate_id}`}>{match.candidate_name}</Link></td>
                  <td><span className="score-badge">{Number(match.overall_score || 0).toFixed(1)}%</span></td>
                  <td><span className={`status-badge ${match.predicted_class === 'HIGH' ? 'status-open' : ''}`}>{match.predicted_class === 'HIGH' ? 'Phù hợp cao' : match.predicted_class === 'MEDIUM' ? 'Trung bình' : match.predicted_class === 'LOW' ? 'Thấp' : 'Chấm điểm cơ bản'}</span></td>
                  <td>{match.model_confidence == null ? '—' : `${(Number(match.model_confidence) * 100).toFixed(1)}%`}</td>
                  <td>{Number(match.skill_score || 0).toFixed(1)}%</td>
                  <td><Link className="action-button" to={`/matching/${match.id}`}>Xem đánh giá</Link></td>
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
