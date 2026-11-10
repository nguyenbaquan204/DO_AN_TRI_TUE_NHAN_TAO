import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';

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

  if (loading) return <LoadingState label="Đang tải chi tiết đánh giá..." />;
  if (!match) return <div className="error-box">{error || 'Match not found'}</div>;
  const featureSnapshot = match.feature_snapshot || {};
  const score = Math.round(Number(match.overall_score || 0));
  const featureLabels = {
    required_skill_match_ratio: 'Tỷ lệ kỹ năng bắt buộc phù hợp',
    preferred_skill_match_ratio: 'Tỷ lệ kỹ năng ưu tiên phù hợp',
    required_skill_matched_count: 'Số kỹ năng bắt buộc đã khớp',
    required_skill_missing_count: 'Số kỹ năng bắt buộc còn thiếu',
    preferred_skill_matched_count: 'Số kỹ năng ưu tiên đã khớp',
    candidate_experience_years: 'Kinh nghiệm ứng viên (năm)',
    required_experience_years: 'Kinh nghiệm yêu cầu (năm)',
    experience_gap: 'Chênh lệch kinh nghiệm (năm)',
    experience_match_ratio: 'Mức đáp ứng kinh nghiệm',
    education_level_match: 'Mức phù hợp học vấn',
    project_relevance: 'Mức liên quan của dự án',
    tfidf_similarity: 'Tương đồng nội dung (TF-IDF)',
    semantic_similarity: 'Tương đồng ngữ nghĩa',
    semantic_model_available: 'Mô hình ngữ nghĩa khả dụng',
    semantic_model_name: 'Mô hình ngữ nghĩa',
    matching_method: 'Phương pháp xếp hạng',
    tfidf_score: 'Điểm tương đồng TF-IDF',
    semantic_score: 'Điểm tương đồng ngữ nghĩa',
    score_weights: 'Tỷ trọng các tiêu chí',
    major_match: 'Phù hợp chuyên ngành',
    certificate_match_ratio: 'Tỷ lệ chứng chỉ phù hợp',
    language_match_ratio: 'Tỷ lệ ngôn ngữ phù hợp',
  };
  const percentageFeatures = new Set([
    'required_skill_match_ratio', 'preferred_skill_match_ratio', 'experience_match_ratio',
    'education_level_match', 'project_relevance', 'tfidf_similarity', 'semantic_similarity',
    'certificate_match_ratio', 'language_match_ratio',
  ]);
  const formattedFeature = (name, value) => {
    if (name === 'semantic_model_available') return value ? 'Có' : 'Không';
    if (name === 'matching_method') {
      return ({
        'hybrid-e5-tfidf': 'Kết hợp E5 và TF-IDF',
        'tfidf-fallback': 'TF-IDF (dự phòng)',
        'tfidf-baseline': 'TF-IDF (mốc so sánh)',
      })[value] || value;
    }
    if (name === 'score_weights' && value && typeof value === 'object') {
      return Object.entries(value).map(([key, weight]) => `${key}: ${(Number(weight) * 100).toFixed(0)}%`).join(' · ');
    }
    if (value === null || value === undefined || value === '') return 'Chưa có dữ liệu';
    if (typeof value === 'boolean') return value ? 'Có' : 'Không';
    if (name === 'tfidf_score' || name === 'semantic_score') return `${Number(value).toFixed(1)}%`;
    if (typeof value === 'number') return `${(value * (percentageFeatures.has(name) ? 100 : 1)).toFixed(1)}${percentageFeatures.has(name) ? '%' : ''}`;
    return Array.isArray(value) ? value.join(', ') : String(value);
  };
  const statusLabel = (status) => status === 'MATCHED' ? 'Đã khớp' : status === 'MISSING' ? 'Còn thiếu' : status === 'ADDITIONAL' ? 'Kỹ năng bổ sung' : status;
  const matchingMethod = featureSnapshot.matching_method;

  return (
    <div className="matching-detail-page">
      <div className="page-heading">
        <div><div className="eyebrow">KẾT QUẢ SÀNG LỌC</div><h1 className="page-title">Chi tiết đánh giá phù hợp</h1><p className="muted">Các yếu tố được dùng để tham khảo mức độ phù hợp giữa CV và vị trí.</p></div>
        <div className="page-actions">
          <Link className="ghost-button" to={`/jobs/${match.job_id}/candidates`}>Quay lại xếp hạng</Link>
          {candidate ? <Link className="ghost-button" to={`/candidates/${candidate.id}`}>Mở hồ sơ CV</Link> : null}
        </div>
      </div>
      {error ? <div className="error-box">{error}</div> : null}

      {featureSnapshot.data_status === 'insufficient-data' ? <div className="error-box">Chưa đủ thông tin CV hoặc yêu cầu tuyển dụng để đánh giá. Hãy bổ sung thông tin và sàng lọc lại.</div> : null}
      {featureSnapshot.scoring_version !== 'reviewed-profile-v2' ? <div className="muted">Kết quả được lưu bằng cách chấm cũ. Hãy sàng lọc lại để áp dụng thông tin đã duyệt.</div> : null}
      <div className="card match-summary-card">
        <div className="match-summary">
          <div className="match-score-ring" style={{ '--score-angle': `${Math.max(0, Math.min(100, score)) * 3.6}deg` }}><div><strong>{score}%</strong><small>phù hợp</small></div></div>
          <div className="match-summary-copy">
            <span className={`status-badge ${match.predicted_class === 'HIGH' ? 'status-open' : ''}`}>{match.predicted_class === 'HIGH' ? 'Phù hợp cao' : match.predicted_class === 'MEDIUM' ? 'Phù hợp trung bình' : match.predicted_class === 'LOW' ? 'Phù hợp thấp' : 'Điểm tham khảo'}</span>
            <h2>{candidate ? candidate.full_name : 'Ứng viên'}</h2>
            <p className="muted">Điểm tổng hợp từ kỹ năng, kinh nghiệm, học vấn và nội dung CV.</p>
            <div className="match-method-note">
              {matchingMethod === 'hybrid-e5-tfidf'
                ? `Xếp hạng kết hợp multilingual-e5-small và TF-IDF cùng các tiêu chí có thể giải thích${featureSnapshot.semantic_model_name ? ` · ${featureSnapshot.semantic_model_name}` : ''}.`
                : matchingMethod === 'tfidf-fallback'
                  ? 'Mô hình ngữ nghĩa chưa sẵn sàng; kết quả này dùng TF-IDF và các tiêu chí có thể giải thích.'
                  : 'Kết quả được xếp hạng theo điểm và bằng chứng trích xuất.'}
              {match.prediction_mode === 'trained-model' ? ' Nhãn Random Forest là tín hiệu tham khảo riêng.' : ''}
            </div>
          </div>
        </div>
        <div className="stats-grid">
          <div className="stat-box"><div className="stat-label">Kỹ năng</div><div className="stat-value">{Number(match.skill_score || 0).toFixed(1)}%</div></div>
          <div className="stat-box"><div className="stat-label">Kinh nghiệm</div><div className="stat-value">{Number(match.experience_score || 0).toFixed(1)}%</div></div>
          <div className="stat-box"><div className="stat-label">Học vấn</div><div className="stat-value">{Number(match.education_score || 0).toFixed(1)}%</div></div>
          <div className="stat-box"><div className="stat-label">Dự án</div><div className="stat-value">{Number(match.project_score || 0).toFixed(1)}%</div></div>
        </div>
        <p className="human-review-note">Điểm này giúp sắp xếp hồ sơ để xem xét. Hãy kiểm tra nội dung CV trước khi đưa ra quyết định tuyển dụng.</p>
      </div>

      <div className="card evidence-card">
        <div className="section-heading"><div><h2>Bằng chứng dùng để chấm điểm</h2><p>Các chỉ số được lưu cùng kết quả lần đánh giá này.</p></div></div>
        {Object.keys(featureSnapshot).length ? <div className="evidence-grid">{Object.entries(featureSnapshot).map(([name, value]) => <div className="evidence-item" key={name}><span>{featureLabels[name] || name.replaceAll('_', ' ')}</span><strong>{formattedFeature(name, value)}</strong></div>)}</div> : <p className="muted">Không có dữ liệu chỉ số chi tiết cho lần đánh giá này.</p>}
      </div>
      <div className="card">
        <div className="section-heading"><div><h2>Giải thích theo kỹ năng</h2><p>Đối chiếu yêu cầu vị trí với kỹ năng phát hiện trong CV.</p></div></div>
        <ul>
          {(match.details || []).filter((item) => item.status === 'MATCHED').map((item) => <li key={`why-${item.skill_name}`}>CV có kỹ năng {item.skill_name} theo yêu cầu vị trí.</li>)}
          {featureSnapshot.experience_match_ratio >= 1 ? <li>Kinh nghiệm phát hiện đáp ứng yêu cầu vị trí.</li> : null}
          {featureSnapshot.education_level_match >= 1 ? <li>Thông tin học vấn phù hợp với yêu cầu.</li> : null}
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
                  <span className={`status-badge ${detail.status === 'MATCHED' ? 'status-open' : detail.status === 'MISSING' ? 'status-missing' : ''}`}>{statusLabel(detail.status)}</span>
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
