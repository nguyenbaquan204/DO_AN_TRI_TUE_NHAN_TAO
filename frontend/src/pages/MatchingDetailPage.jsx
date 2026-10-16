import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function MatchingDetailPage() {
  const { matchId } = useParams();
  const [match, setMatch] = useState(null);
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadMatch = async () => {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      try {
        const matchRes = await axios.get(`${API_URL}/api/matching/matches/${matchId}`, { headers });
        setMatch(matchRes.data);
        const candidateRes = await axios.get(`${API_URL}/api/candidates/${matchRes.data.candidate_id}`, { headers });
        setCandidate(candidateRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load match detail');
      } finally {
        setLoading(false);
      }
    };

    loadMatch();
  }, [matchId]);

  if (loading) return <div>Đang tải chi tiết đánh giá...</div>;
  if (!match) return <div className="error-box">{error || 'Match not found'}</div>;
  const featureSnapshot = match.feature_snapshot || {};

  return (
    <div>
      <div className="page-title">Chi tiết kết quả phù hợp</div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="page-actions" style={{ marginBottom: 16 }}>
        <Link className="ghost-button" to={`/jobs/${match.job_id}/candidates`}>Quay lại xếp hạng</Link>
        {candidate ? <Link className="ghost-button" to={`/candidates/${candidate.id}`}>Hồ sơ ứng viên</Link> : null}
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3>{candidate ? candidate.full_name : 'Ứng viên'} · điểm phù hợp {Number(match.overall_score || 0).toFixed(1)}%</h3>
        <p><strong>Nhãn mô hình:</strong> {match.predicted_class || 'Chưa có dự đoán mô hình'}</p>
        <p className="muted">{match.model_confidence == null ? 'Dự đoán dự phòng theo luật' : `Độ tin cậy mô hình: ${(Number(match.model_confidence) * 100).toFixed(1)}%`}</p>
        <p><strong>Cách sàng lọc:</strong> {match.prediction_mode === 'trained-model' ? 'Random Forest (tham khảo)' : 'Chấm điểm theo bằng chứng'}</p>
        <p><strong>Phiên bản mô hình:</strong> {match.model_version || 'Không có'}</p>
        <p><strong>Chế độ dự đoán:</strong> {match.prediction_mode || 'Không có'}</p>
        <div className="stats-grid">
          <div className="stat-box"><div className="stat-label">Kỹ năng</div><div className="stat-value">{Number(match.skill_score || 0).toFixed(1)}%</div></div>
          <div className="stat-box"><div className="stat-label">{featureSnapshot.semantic_model_available ? 'Mức tương đồng ngữ nghĩa' : 'Ngữ nghĩa (chưa khả dụng)'}</div><div className="stat-value">{featureSnapshot.semantic_model_available ? `${Number(match.semantic_score || 0).toFixed(1)}%` : '—'}</div></div>
          <div className="stat-box"><div className="stat-label">Kinh nghiệm</div><div className="stat-value">{Number(match.experience_score || 0).toFixed(1)}%</div></div>
          <div className="stat-box"><div className="stat-label">Học vấn</div><div className="stat-value">{Number(match.education_score || 0).toFixed(1)}%</div></div>
        </div>
      </div>

      <div className="card">
        <h3>Bằng chứng dùng để chấm điểm</h3>
        <div className="grid-two">{Object.entries(featureSnapshot).map(([name, value]) => <div key={name}><strong>{name}:</strong> {name === 'semantic_similarity' && featureSnapshot.semantic_model_available === false ? 'Unavailable' : value === null ? 'Unavailable' : typeof value === 'number' ? value.toFixed(3) : String(value)}</div>)}</div>
      </div>
      <div className="card">
        <h3>Vì sao hồ sơ nhận điểm này</h3>
        <ul>
          {(match.details || []).filter((item) => item.status === 'MATCHED').map((item) => <li key={`why-${item.skill_name}`}>Có kỹ năng {item.skill_name}</li>)}
          {featureSnapshot.experience_match_ratio >= 1 ? <li>Đạt yêu cầu kinh nghiệm tối thiểu</li> : null}
          {featureSnapshot.education_level_match >= 1 ? <li>Phù hợp yêu cầu học vấn</li> : null}
        </ul>
        {match.details && match.details.length ? (
          <div className="stack">
            {match.details.map((detail, index) => (
              <div key={`${detail.skill_name}-${index}`} className="list-item-row">
                <div>
                  <strong>{detail.skill_name}</strong>
                  <div className="muted">{detail.description || 'Đánh giá kỹ năng'}</div>
                </div>
                <div className="row-actions">
                  <span className="badge">{detail.status}</span>
                  <span>{Number(detail.score || 0)}%</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="muted">Chưa có yếu tố chi tiết cho kết quả này.</div>
        )}
      </div>
    </div>
  );
}
