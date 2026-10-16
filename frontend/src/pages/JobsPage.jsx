import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const emptyForm = { title: '', department: '', location: '', description: '', employment_type: 'Full-time', experience_required: '', education_required: '', education_level: '', majors: '', required_skills: '', preferred_skills: '', maximum_experience_years: '', required_certificates: '', preferred_certificates: '', required_languages: '', preferred_languages: '', relevant_experience_required: false, salary: '', status: 'open' };
const list = (value) => String(value || '').split(',').map((item) => item.trim()).filter(Boolean);
const asList = (value) => (Array.isArray(value) ? value : []);
const getErrorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg).filter(Boolean);
    if (messages.length) return messages.join(' ');
  }
  return fallback;
};
const formFromJob = (job) => ({
  ...emptyForm,
  ...job,
  majors: asList(job.majors).join(', '),
  required_skills: asList(job.required_skills).join(', '),
  preferred_skills: asList(job.preferred_skills).join(', '),
  required_certificates: asList(job.required_certificates).join(', '),
  preferred_certificates: asList(job.preferred_certificates).join(', '),
  required_languages: asList(job.required_languages).join(', '),
  preferred_languages: asList(job.preferred_languages).join(', '),
  maximum_experience_years: job.maximum_experience_years ?? '',
  relevant_experience_required: Boolean(job.relevant_experience_required),
});

export default function JobsPage() {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const editing = Boolean(jobId);
  const [jobs, setJobs] = useState([]);
  const [form, setForm] = useState({ ...emptyForm });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');

  const fetchJobs = async () => {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/api/jobs`, { headers: { Authorization: `Bearer ${token}` } });
    setJobs(Array.isArray(response.data) ? response.data : []);
  };

  useEffect(() => {
    const load = async () => {
      try {
        if (editing) {
          const token = localStorage.getItem('token');
          const response = await axios.get(`${API_URL}/api/jobs/${jobId}`, { headers: { Authorization: `Bearer ${token}` } });
          setForm(formFromJob(response.data));
        } else {
          await fetchJobs();
        }
      } catch (err) {
        setError(getErrorMessage(err, editing ? 'Không thể tải vị trí tuyển dụng' : 'Không thể tải danh sách vị trí tuyển dụng'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [editing, jobId]);

  const setField = (name, value) => setForm((current) => ({ ...current, [name]: value }));
  const openJobCount = jobs.filter((job) => job.status === 'open').length;
  const closedJobCount = jobs.length - openJobCount;
  const visibleJobs = statusFilter === 'all' ? jobs : jobs.filter((job) => job.status === statusFilter);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.title.trim() || !form.description.trim()) {
      setError('Vui lòng nhập tên vị trí và mô tả công việc.');
      return;
    }
    if (form.description.trim().length < 10) {
      setError('Mô tả công việc cần có ít nhất 10 ký tự.');
      return;
    }
    setSubmitting(true);
    setError('');
    const token = localStorage.getItem('token');
    const payload = {
      ...form,
      required_skills: list(form.required_skills),
      preferred_skills: list(form.preferred_skills),
      majors: list(form.majors),
      required_certificates: list(form.required_certificates),
      preferred_certificates: list(form.preferred_certificates),
      required_languages: list(form.required_languages),
      preferred_languages: list(form.preferred_languages),
      maximum_experience_years: form.maximum_experience_years === '' ? null : Number(form.maximum_experience_years),
    };
    try {
      const response = editing
        ? await axios.put(`${API_URL}/api/jobs/${jobId}`, payload, { headers: { Authorization: `Bearer ${token}` } })
        : await axios.post(`${API_URL}/api/jobs`, payload, { headers: { Authorization: `Bearer ${token}` } });
      if (response.data?.id) navigate(`/jobs/${response.data.id}`);
    } catch (err) {
      setError(getErrorMessage(err, editing ? 'Cập nhật vị trí tuyển dụng thất bại' : 'Tạo vị trí tuyển dụng thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="muted">Đang tải vị trí tuyển dụng...</div>;
  return (
    <div>
      <div className="page-title">{editing ? 'Chỉnh sửa vị trí tuyển dụng' : 'Vị trí tuyển dụng'}</div>
      {error ? <div className="error-box">{error}</div> : null}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>{editing ? 'Cập nhật vị trí tuyển dụng' : 'Tạo vị trí tuyển dụng'}</h3>
        <form className="form-grid" onSubmit={handleSubmit}>
          <h4>Thông tin vị trí</h4>
          <div className="form-row"><input className="input" name="title" value={form.title} placeholder="Tên vị trí" minLength={2} required onChange={(e) => setField('title', e.target.value)} /><input className="input" name="department" value={form.department} placeholder="Phòng ban" onChange={(e) => setField('department', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="location" value={form.location} placeholder="Địa điểm" onChange={(e) => setField('location', e.target.value)} /><input className="input" name="employment_type" value={form.employment_type} placeholder="Hình thức làm việc" onChange={(e) => setField('employment_type', e.target.value)} /></div>
          <h4>Kỹ năng và học vấn</h4>
          <div className="form-row"><input className="input" name="required_skills" value={form.required_skills} placeholder="Kỹ năng bắt buộc, phân cách bằng dấu phẩy" onChange={(e) => setField('required_skills', e.target.value)} /><input className="input" name="preferred_skills" value={form.preferred_skills} placeholder="Kỹ năng ưu tiên" onChange={(e) => setField('preferred_skills', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="education_level" value={form.education_level} placeholder="Trình độ học vấn" onChange={(e) => setField('education_level', e.target.value)} /><input className="input" name="majors" value={form.majors} placeholder="Chuyên ngành" onChange={(e) => setField('majors', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="experience_required" value={form.experience_required} placeholder="Kinh nghiệm yêu cầu" onChange={(e) => setField('experience_required', e.target.value)} /><input className="input" name="maximum_experience_years" type="number" value={form.maximum_experience_years} placeholder="Kinh nghiệm tối đa" onChange={(e) => setField('maximum_experience_years', e.target.value)} /></div>
          <label><input type="checkbox" checked={form.relevant_experience_required} onChange={(e) => setField('relevant_experience_required', e.target.checked)} /> Yêu cầu kinh nghiệm liên quan</label>
          <h4>Chứng chỉ và ngôn ngữ</h4>
          <div className="form-row"><input className="input" name="required_certificates" value={form.required_certificates} placeholder="Chứng chỉ bắt buộc" onChange={(e) => setField('required_certificates', e.target.value)} /><input className="input" name="preferred_certificates" value={form.preferred_certificates} placeholder="Chứng chỉ ưu tiên" onChange={(e) => setField('preferred_certificates', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="required_languages" value={form.required_languages} placeholder="Ngôn ngữ bắt buộc" onChange={(e) => setField('required_languages', e.target.value)} /><input className="input" name="preferred_languages" value={form.preferred_languages} placeholder="Ngôn ngữ ưu tiên" onChange={(e) => setField('preferred_languages', e.target.value)} /></div>
          <h4>Mô tả công việc</h4>
          <textarea className="input" name="description" value={form.description} placeholder="Mô tả công việc (ít nhất 10 ký tự)" rows={4} minLength={10} required onChange={(e) => setField('description', e.target.value)} />
          <div className="page-actions"><Link className="ghost-button" to={editing ? `/jobs/${jobId}` : '/jobs'}>Hủy</Link><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Đang lưu...' : 'Lưu vị trí tuyển dụng'}</button></div>
        </form>
      </div>
      {!editing ? <div className="card">
        <div className="page-actions" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span className="muted">{visibleJobs.length} vị trí đang hiển thị · {openJobCount} đang tuyển · {closedJobCount} đã đóng</span>
          <select className="input" aria-label="Lọc vị trí tuyển dụng" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={{ width: 'auto', minWidth: 190 }}>
            <option value="open">Đang tuyển ({openJobCount})</option>
            <option value="closed">Đã đóng ({closedJobCount})</option>
            <option value="all">Tất cả vị trí ({jobs.length})</option>
          </select>
        </div>
        <div className="table-wrap"><table className="table"><thead><tr><th>Vị trí</th><th>Phòng ban</th><th>Địa điểm</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{visibleJobs.length ? visibleJobs.map((job) => <tr key={job.id}><td><strong>{job.title}</strong></td><td>{job.department || '-'}</td><td>{job.location || '-'}</td><td><span className={`status-badge ${job.status === 'open' ? 'status-open' : ''}`}>{job.status === 'open' ? 'Đang tuyển' : 'Đã đóng'}</span></td><td><div className="table-actions"><Link className="action-button" to={`/jobs/${job.id}`}>Chi tiết</Link><Link className="action-button" to={`/jobs/${job.id}/edit`}>Chỉnh sửa</Link><Link className="action-button action-button-primary" to={`/jobs/${job.id}/candidates`}>Xếp hạng ứng viên</Link></div></td></tr>) : <tr><td colSpan="5" className="muted">Không có vị trí trong bộ lọc này.</td></tr>}</tbody></table></div>
      </div> : null}
    </div>
  );
}
