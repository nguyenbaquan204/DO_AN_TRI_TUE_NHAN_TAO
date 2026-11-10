import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';
import ConfirmDialog from '../components/ConfirmDialog';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const auth = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });
const splitList = (value) => String(value || '').split(/[,;\n]/).map((item) => item.trim()).filter(Boolean);

export default function JobDetailPage() {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [uploadingJd, setUploadingJd] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [applying, setApplying] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

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
    setUploadingJd(true);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/jobs/${jobId}/upload-jd`, data, { headers: auth() });
      const parsed = response.data?.suggestions || null;
      setSuggestions(parsed ? {
        ...parsed,
        description: response.data.description || '',
        required_skills_text: (parsed.required_skills?.length ? parsed.required_skills : (job.required_skills || [])).join(', '),
        preferred_skills_text: (parsed.preferred_skills?.length ? parsed.preferred_skills : (job.preferred_skills || [])).join(', '),
        required_languages_text: (parsed.languages?.length ? parsed.languages : (job.required_languages || [])).join(', '),
        experience_required: Number(parsed.experience_years) > 0 ? `${parsed.experience_years} years` : (job.experience_required || ''),
        education_required: parsed.education_required || job.education_required || '',
      } : null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Tải JD thất bại');
    } finally {
      setUploadingJd(false);
    }
  };

  const applySuggestions = async () => {
    if (!suggestions || !job) return;
    setApplying(true);
    setError('');
    try {
      const response = await axios.put(`${API_URL}/api/jobs/${jobId}`, {
        ...job,
        description: suggestions.description?.trim() ? suggestions.description.trim() : job.description,
        required_skills: splitList(suggestions.required_skills_text),
        preferred_skills: splitList(suggestions.preferred_skills_text),
        required_languages: splitList(suggestions.required_languages_text),
        experience_required: suggestions.experience_required,
        education_required: suggestions.education_required,
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

  const deleteJob = async () => {
    setDeleting(true);
    setError('');
    try {
      await axios.delete(`${API_URL}/api/jobs/${jobId}`, { headers: auth() });
      navigate('/jobs', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể xóa vị trí tuyển dụng. Vui lòng thử lại.');
      setDeleteDialogOpen(false);
    }
    setDeleting(false);
  };

  if (loading) return <LoadingState label="Đang tải thông tin vị trí..." />;
  if (!job) return <div className="error-box">{error || 'Không tìm thấy vị trí tuyển dụng'}</div>;
  const values = (value) => (Array.isArray(value) ? value : []).join(', ') || '-';

  return (
    <div className="job-detail-page">
      <div className="page-heading job-detail-heading">
        <div><div className="eyebrow">CHI TIẾT VỊ TRÍ</div><h1 className="page-title">{job.title}</h1><p className="muted">{[job.company_name, job.department, job.location].filter(Boolean).join(' · ') || 'Thông tin tuyển dụng'}</p></div>
        <span className={`status-badge ${job.status === 'open' ? 'status-open' : 'status-closed'}`}>{job.status === 'open' ? 'Đang tuyển' : 'Đã đóng'}</span>
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="page-actions job-detail-actions">
        <Link className="ghost-button" to="/jobs">Tất cả vị trí</Link>
        <Link className="ghost-button" to={`/jobs/${jobId}/edit`}>Chỉnh sửa</Link>
        <button className="action-button action-button-danger" type="button" onClick={() => setDeleteDialogOpen(true)} disabled={deleting}>Xóa vị trí</button>
        <button className="ghost-button" type="button" onClick={handleAnalyze} disabled={analyzing}>{analyzing ? <><span className="loading-spinner loading-spinner-small" aria-hidden="true" />Đang phân tích...</> : 'Phân tích JD'}</button>
        <Link className="primary-button" to={`/jobs/${jobId}/candidates`}>Xếp hạng ứng viên</Link>
        <Link className="primary-button" to={`/jobs/${jobId}/upload-candidates`}>+ Tải CV cho vị trí</Link>
      </div>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Yêu cầu tuyển dụng</h3>
        <div className="grid-two">
          <div><strong>Công ty:</strong> {job.company_name || '-'}</div>
          <div><strong>Phòng ban:</strong> {job.department || '-'}</div><div><strong>Địa điểm:</strong> {job.location || '-'}</div>
          <div><strong>Mức lương:</strong> {job.salary || '-'}</div>
          <div><strong>Hình thức:</strong> {job.employment_type || '-'}</div><div><strong>Kinh nghiệm:</strong> {job.experience_required || '-'}</div>
          <div><strong>Học vấn:</strong> {job.education_required || '-'}</div><div><strong>Trình độ:</strong> {job.education_level || '-'}</div>
          <div><strong>Chuyên ngành:</strong> {values(job.majors)}</div><div><strong>Kinh nghiệm tối đa:</strong> {job.maximum_experience_years ?? '-'}</div>
          <div><strong>Kinh nghiệm liên quan:</strong> {job.relevant_experience_required ? 'Bắt buộc' : 'Không bắt buộc'}</div>
          <div><strong>Kỹ năng bắt buộc:</strong> {values(job.required_skills)}</div><div><strong>Kỹ năng ưu tiên:</strong> {values(job.preferred_skills)}</div>
          <div><strong>Chứng chỉ bắt buộc:</strong> {values(job.required_certificates)}</div><div><strong>Chứng chỉ ưu tiên:</strong> {values(job.preferred_certificates)}</div>
          <div><strong>Ngôn ngữ bắt buộc:</strong> {values(job.required_languages)}</div><div><strong>Ngôn ngữ ưu tiên:</strong> {values(job.preferred_languages)}</div>
        </div>
        <div className="card" style={{ marginBottom: 24 }}><h3>Tải JD và xem đề xuất</h3><div className="form-row"><input className="input" type="file" accept=".pdf,.docx,.txt" aria-label="Chọn file JD để phân tích" onChange={(event) => setJdFile(event.target.files?.[0] || null)} /><button className="primary-button" type="button" onClick={handleJdUpload} disabled={!jdFile || uploadingJd}>{uploadingJd ? <><span className="button-spinner" aria-hidden="true" />Đang phân tích...</> : 'Phân tích JD tải lên'}</button></div>
          {suggestions ? <div className="jd-review-panel">
            <div className="jd-review-heading"><strong>Kiểm tra nội dung và đề xuất trích xuất</strong><span>Chưa lưu cho đến khi bạn chọn áp dụng</span></div>
            <label className="cv-review-field cv-review-field-full">Mô tả công việc đã đọc<textarea className="input" rows={7} value={suggestions.description} onChange={(event) => setSuggestions((current) => ({ ...current, description: event.target.value }))} /></label>
            <div className="cv-review-grid" style={{ marginTop: 12 }}>
              <label className="cv-review-field">Kỹ năng bắt buộc<input className="input" value={suggestions.required_skills_text} onChange={(event) => setSuggestions((current) => ({ ...current, required_skills_text: event.target.value }))} /></label>
              <label className="cv-review-field">Kỹ năng ưu tiên<input className="input" value={suggestions.preferred_skills_text} onChange={(event) => setSuggestions((current) => ({ ...current, preferred_skills_text: event.target.value }))} /></label>
              <label className="cv-review-field">Kinh nghiệm yêu cầu<input className="input" value={suggestions.experience_required} onChange={(event) => setSuggestions((current) => ({ ...current, experience_required: event.target.value }))} /></label>
              <label className="cv-review-field">Học vấn yêu cầu<input className="input" value={suggestions.education_required} onChange={(event) => setSuggestions((current) => ({ ...current, education_required: event.target.value }))} /></label>
              <label className="cv-review-field cv-review-field-full">Ngôn ngữ bắt buộc<input className="input" value={suggestions.required_languages_text} onChange={(event) => setSuggestions((current) => ({ ...current, required_languages_text: event.target.value }))} /></label>
            </div>
            <button className="primary-button" type="button" onClick={applySuggestions} disabled={applying} style={{ marginTop: 14 }}>{applying ? <><span className="button-spinner" aria-hidden="true" />Đang áp dụng...</> : 'Áp dụng nội dung đã kiểm tra'}</button>
          </div> : null}
        </div>
        <strong>Mô tả công việc</strong><p className="muted">{job.description || '-'}</p>
      </div>
      <div className="card"><h3>Phân tích JD</h3>{analysis ? <div className="stack">{analysis.summary ? <p>{analysis.summary}</p> : null}{Array.isArray(analysis.required_skills) && analysis.required_skills.length ? <div><strong>Kỹ năng bắt buộc</strong><div className="tag-list">{analysis.required_skills.map((skill) => <span key={skill} className="pill">{skill}</span>)}</div></div> : null}{Array.isArray(analysis.soft_skills) && analysis.soft_skills.length ? <div><strong>Kỹ năng mềm</strong><div className="tag-list">{analysis.soft_skills.map((skill) => <span key={skill} className="pill">{skill}</span>)}</div></div> : null}{analysis.experience_years !== undefined ? <div><strong>Kinh nghiệm tham khảo:</strong> {analysis.experience_years}</div> : null}</div> : <div className="muted">Chưa có phân tích JD.</div>}</div>
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Xóa vị trí tuyển dụng?"
        description={`Vị trí “${job.title}” và các kết quả đánh giá liên quan sẽ bị xóa. Hồ sơ ứng viên và CV vẫn được giữ lại.`}
        busy={deleting}
        onCancel={() => setDeleteDialogOpen(false)}
        onConfirm={deleteJob}
      />
    </div>
  );
}
