import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function CandidateDetailPage() {
  const params = useParams();
  const id = params.id || params.candidateId;
  const backToCandidates = params.jobId ? `/jobs/${params.jobId}/candidates` : '/candidates';
  const [candidate, setCandidate] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [matchData, setMatchData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);
  const experienceYears = Number(candidate?.experience_years || 0);
  const experienceLabel = experienceYears <= 0 ? '0 năm' : experienceYears < 1
    ? `${Math.round(experienceYears * 12)} tháng`
    : `${Number(experienceYears.toFixed(1))} năm`;

  const loadCandidateData = async () => {
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [candidateRes, jobsRes] = await Promise.all([
        axios.get(`${API_URL}/api/candidates/${id}`, { headers }),
        axios.get(`${API_URL}/api/jobs`, { headers }),
      ]);
      setCandidate(candidateRes.data);
      setJobs((jobsRes.data || []).filter((job) => job.status === 'open'));

      const jobMatches = [];
      for (const job of jobsRes.data || []) {
        try {
          const matchRes = await axios.get(`${API_URL}/api/matching/jobs/${job.id}/matches`, { headers });
          const match = (matchRes.data || []).find((item) => Number(item.candidate_id) === Number(id));
          if (match) {
            jobMatches.push({ ...match, job_id: job.id, job_title: job.title });
          }
        } catch (innerErr) {
          console.warn(`No matching data for job ${job.id}`, innerErr);
        }
      }
      setMatchData(jobMatches);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load candidate');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    setError('');
    loadCandidateData();
  }, [id]);

  const generateMatch = async (jobId) => {
    const token = localStorage.getItem('token');
    setGenerating(true);
    try {
      await axios.post(`${API_URL}/api/matching/jobs/${jobId}/match/${id}`, {}, { headers: { Authorization: `Bearer ${token}` } });
      await loadCandidateData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Matching failed');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div>Đang tải ứng viên...</div>;
  if (!candidate) return <div className="error-box">{error || 'Không tìm thấy ứng viên'}</div>;

  return (
    <div>
      <div className="page-title">Chi tiết ứng viên</div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="page-actions" style={{ marginBottom: 16 }}>
        <Link className="ghost-button" to={backToCandidates}>Quay lại danh sách ứng viên</Link>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Thông tin cá nhân</h3>
        <h2>{candidate.full_name}</h2>
        <div className="grid-two">
          <div><strong>Email:</strong> {candidate.email || 'Chưa cung cấp'}</div>
          <div><strong>Điện thoại:</strong> {candidate.phone || 'Chưa cung cấp'}</div>
          <div><strong>Địa điểm:</strong> {candidate.location || 'Chưa cung cấp'}</div>
          <div><strong>LinkedIn:</strong> {candidate.linkedin ? <a href={candidate.linkedin} target="_blank" rel="noreferrer">Mở hồ sơ</a> : 'Không có'}</div>
          <div><strong>GitHub:</strong> {candidate.github || 'Không có'}</div>
          <div><strong>Portfolio:</strong> {candidate.portfolio || 'Không có'}</div>
        </div>
      </div>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Kỹ năng</h3>
        <div className="tag-list">{(candidate.skills || []).map((skill) => <span className="pill" key={skill}>{skill}</span>)}</div>
        {!candidate.skills?.length ? <p className="muted">Chưa phát hiện kỹ năng.</p> : null}
        <h3>Học vấn</h3><p>{candidate.education?.text || 'Chưa phát hiện'}</p>
        <h3>Kinh nghiệm</h3><p>{experienceLabel} được phát hiện</p>
        {candidate.work_experience?.text ? <div className="cv-experience">{candidate.work_experience.text}</div> : null}
        <h3>Dự án</h3>{candidate.projects?.length ? <ul>{candidate.projects.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">Chưa phát hiện dự án.</p>}
        <h3>Chứng chỉ</h3>{candidate.certificates?.length ? <ul>{candidate.certificates.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">Chưa phát hiện chứng chỉ.</p>}
        <h3>Ngôn ngữ</h3><p>{(candidate.languages || []).join(', ') || 'Chưa phát hiện'}</p>
        <h3>CV gốc</h3><pre className="muted">{candidate.raw_text || 'Không có nội dung trích xuất'}</pre>
      </div>

      <div className="card">
        <h3>Điểm phù hợp theo vị trí</h3>
        {jobs.length ? (
          <div className="stack">
            {jobs.map((job) => {
              const existing = matchData.find((match) => Number(match.job_id) === Number(job.id));
              return (
                <div key={job.id} className="list-item-row">
                  <div>
                    <strong>{job.title}</strong>
                    <div className="muted">{job.department || 'Chung'} · {job.location || 'Từ xa'}</div>
                  </div>
                  <div className="row-actions">
                    {existing ? (
                      <>
                        <span className="badge">{Number(existing.overall_score || 0).toFixed(1)}%</span>
                        <Link to={`/matching/${existing.id}`}>Xem chi tiết</Link>
                      </>
                    ) : (
                      <button className="primary-button" disabled={generating} onClick={() => generateMatch(job.id)}>
                        {generating ? 'Đang chấm điểm...' : 'Tạo điểm phù hợp'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="muted">Chưa có vị trí để chấm điểm ứng viên.</div>
        )}
      </div>
    </div>
  );
}
