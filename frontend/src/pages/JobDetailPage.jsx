import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const auth = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

export default function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [applying, setApplying] = useState(false);

  const loadJob = async () => {
    setLoading(true);
    setError('');
    try {
      const jobRes = await axios.get(`${API_URL}/api/jobs/${jobId}`, { headers: auth() });
      setJob(jobRes.data);
      try {
        const analysisRes = await axios.get(`${API_URL}/api/jobs/${jobId}/analysis`, { headers: auth() });
        setAnalysis(analysisRes.data);
      } catch {
        setAnalysis(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể tải chi tiết vị trí tuyển dụng');
      setJob(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadJob(); }, [jobId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const res = await axios.post(`${API_URL}/api/jobs/${jobId}/analyze`, {}, { headers: auth() });
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Phân tích JD thất bại');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleJdUpload = async () => {
    if (!jdFile) return;
    const data = new FormData();
    data.append('file', jdFile);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/jobs/${jobId}/upload-jd`, data, { headers: auth() });
      setSuggestions(response.data?.suggestions || null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Tải JD thất bại');
    }
  };

  const applySuggestions = async () => {
    if (!suggestions || !job) return;
    setApplying(true);
    setError('');
    try {
      const response = await axios.put(`${API_URL}/api/jobs/${jobId}`, {
        ...job,
        required_skills: suggestions.required_skills || [],
        preferred_skills: suggestions.preferred_skills || [],
        experience_required: Number(suggestions.experience_years) > 0 ? `${suggestions.experience_years} years` : job.experience_required,
        education_required: suggestions.education_required || job.education_required,
      }, { headers: auth() });
      setJob(response.data);
      setSuggestions(null);
      try {
        const analysisResponse = await axios.get(`${API_URL}/api/jobs/${jobId}/analysis`, { headers: auth() });
        setAnalysis(analysisResponse.data);
      } catch {
        setAnalysis(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Áp dụng đề xuất thất bại');
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <div className="muted">Đang tải vị trí tuyển dụng...</div>;
  if (!job) return <div className="error-box">{error || 'Không tìm thấy vị trí tuyển dụng'}</div>;
  const values = (value) => (Array.isArray(value) ? value : []).join(', ') || '-';

  return (
    <div>
      <div className="page-title">{job.title}</div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="page-actions" style={{ marginBottom: 16 }}>
        <Link className="ghost-button" to="/jobs">Quay lại vị trí tuyển dụng</Link>
        <Link className="ghost-button" to={`/jobs/${jobId}/edit`}>Chỉnh sửa</Link>
        <button className="primary-button" onClick={handleAnalyze} disabled={analyzing}>{analyzing ? 'Đang phân tích...' : 'Phân tích JD'}</button>
        <Link className="primary-button" to={`/jobs/${jobId}/candidates`}>Xem xếp hạng</Link>
        <Link className="primary-button" to={`/jobs/${jobId}/upload-candidates`}>Tải CV</Link>
      </div>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Yêu cầu tuyển dụng</h3>
        <div className="grid-two">
          <div><strong>Phòng ban:</strong> {job.department || '-'}</div><div><strong>Địa điểm:</strong> {job.location || '-'}</div>
          <div><strong>Hình thức:</strong> {job.employment_type || '-'}</div><div><strong>Kinh nghiệm:</strong> {job.experience_required || '-'}</div>
          <div><strong>Học vấn:</strong> {job.education_required || '-'}</div><div><strong>Trình độ:</strong> {job.education_level || '-'}</div>
          <div><strong>Chuyên ngành:</strong> {values(job.majors)}</div><div><strong>Kinh nghiệm tối đa:</strong> {job.maximum_experience_years ?? '-'}</div>
          <div><strong>Kinh nghiệm liên quan:</strong> {job.relevant_experience_required ? 'Bắt buộc' : 'Không bắt buộc'}</div>
          <div><strong>Kỹ năng bắt buộc:</strong> {values(job.required_skills)}</div><div><strong>Kỹ năng ưu tiên:</strong> {values(job.preferred_skills)}</div>
          <div><strong>Chứng chỉ bắt buộc:</strong> {values(job.required_certificates)}</div><div><strong>Chứng chỉ ưu tiên:</strong> {values(job.preferred_certificates)}</div>
          <div><strong>Ngôn ngữ bắt buộc:</strong> {values(job.required_languages)}</div><div><strong>Ngôn ngữ ưu tiên:</strong> {values(job.preferred_languages)}</div>
        </div>
        <div className="card" style={{ marginBottom: 24 }}><h3>Tải JD và xem đề xuất</h3><div className="form-row"><input className="input" type="file" accept=".pdf,.docx,.txt" onChange={(event) => setJdFile(event.target.files?.[0] || null)} /><button className="primary-button" onClick={handleJdUpload} disabled={!jdFile}>Phân tích JD tải lên</button></div>
          {suggestions ? <div className="stack" style={{ marginTop: 16 }}><div><strong>Kỹ năng bắt buộc đề xuất:</strong> {values(suggestions.required_skills)}</div><div><strong>Kỹ năng ưu tiên đề xuất:</strong> {values(suggestions.preferred_skills)}</div><div><strong>Kinh nghiệm đề xuất:</strong> {suggestions.experience_years || 0} năm</div><div><strong>Học vấn đề xuất:</strong> {suggestions.education_required || '-'}</div><button className="primary-button" onClick={applySuggestions} disabled={applying}>{applying ? 'Đang áp dụng...' : 'Áp dụng đề xuất'}</button></div> : null}
        </div>
        <strong>Mô tả công việc</strong><p className="muted">{job.description || '-'}</p>
      </div>
      <div className="card"><h3>Phân tích JD</h3>{analysis ? <div className="stack">{analysis.summary ? <p>{analysis.summary}</p> : null}{Array.isArray(analysis.required_skills) && analysis.required_skills.length ? <div><strong>Kỹ năng bắt buộc</strong><div className="tag-list">{analysis.required_skills.map((skill) => <span key={skill} className="pill">{skill}</span>)}</div></div> : null}{Array.isArray(analysis.soft_skills) && analysis.soft_skills.length ? <div><strong>Kỹ năng mềm</strong><div className="tag-list">{analysis.soft_skills.map((skill) => <span key={skill} className="pill">{skill}</span>)}</div></div> : null}{analysis.experience_years !== undefined ? <div><strong>Kinh nghiệm tham khảo:</strong> {analysis.experience_years}</div> : null}</div> : <div className="muted">Chưa có phân tích JD.</div>}</div>
    </div>
  );
}
