import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';
import ConfirmDialog from '../components/ConfirmDialog';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const emptyForm = { title: '', company_name: '', department: '', location: '', description: '', source_url: '', employment_type: 'Full-time', experience_required: '', education_required: '', education_level: '', majors: '', required_skills: '', preferred_skills: '', maximum_experience_years: '', required_certificates: '', preferred_certificates: '', required_languages: '', preferred_languages: '', relevant_experience_required: false, salary: '', status: 'open' };
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
  const [sourceUrl, setSourceUrl] = useState('');
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState('');
  const [importNote, setImportNote] = useState('');
  const [availablePostings, setAvailablePostings] = useState([]);
  const [selectedPosting, setSelectedPosting] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [pastedJd, setPastedJd] = useState('');
  const [parsingAlternative, setParsingAlternative] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [deletingJobId, setDeletingJobId] = useState(null);
  const [jobToDelete, setJobToDelete] = useState(null);
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

  const deleteJob = (job) => setJobToDelete(job);

  const confirmDeleteJob = async () => {
    if (!jobToDelete) return;
    setDeletingJobId(jobToDelete.id);
    setError('');
    setNotice('');
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/jobs/${jobToDelete.id}`, { headers: { Authorization: `Bearer ${token}` } });
      setJobs((current) => current.filter((item) => item.id !== jobToDelete.id));
      setNotice(`Đã xóa vị trí "${jobToDelete.title}" và các kết quả đánh giá liên quan.`);
      setJobToDelete(null);
    } catch (err) {
      setError(getErrorMessage(err, 'Không thể xóa vị trí tuyển dụng. Vui lòng thử lại.'));
      setJobToDelete(null);
    } finally {
      setDeletingJobId(null);
    }
  };

  const applyDraft = (draft) => {
    setForm((current) => ({
      ...current,
      title: draft.title || current.title,
      company_name: draft.company_name || current.company_name,
      department: draft.department || current.department,
      location: draft.location || current.location,
      employment_type: draft.employment_type || current.employment_type,
      experience_required: draft.experience_required || (draft.experience_years ? `${draft.experience_years}+ năm` : current.experience_required),
      education_required: draft.education_required || current.education_required,
      required_skills: list(draft.required_skills).join(', ') || current.required_skills,
      preferred_skills: list(draft.preferred_skills).join(', ') || current.preferred_skills,
      required_languages: list(draft.required_languages).join(', ') || current.required_languages,
      description: draft.description || current.description,
      source_url: draft.source_url ?? current.source_url,
    }));
    setImportNote(`Đã tạo bản nháp bằng ${draft.extraction_method || 'nội dung cung cấp'}. Hãy rà soát và chỉnh sửa trước khi lưu.`);
    setImportError('');
    setAvailablePostings([]);
  };

  const importJobDescription = async () => {
    if (!sourceUrl.trim()) {
      setImportError('Vui lòng nhập đường dẫn tin tuyển dụng công khai.');
      return;
    }
    setImporting(true);
    setImportError('');
    setImportNote('');
    setAvailablePostings([]);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/jobs/import-url`, { url: sourceUrl.trim() }, { headers: { Authorization: `Bearer ${token}` } });
      const draft = response.data || {};
      if (Array.isArray(draft.postings)) {
        setAvailablePostings(draft.postings);
        setSelectedPosting('0');
        setImportNote(`Tìm thấy ${draft.postings.length} tin công khai. Chọn tin cần nhập.`);
      } else {
        applyDraft({ ...draft, source_url: draft.source_url || sourceUrl.trim() });
      }
    } catch (err) {
      setImportError(getErrorMessage(err, 'Không thể đọc đường dẫn này. Bạn vẫn có thể tải file JD lên hoặc dán nội dung vào bên dưới.'));
    } finally {
      setImporting(false);
    }
  };

  const selectPosting = () => {
    const draft = availablePostings[Number(selectedPosting)];
    if (draft) applyDraft(draft);
  };

  const parseJdFile = async () => {
    if (!jdFile) {
      setImportError('Hãy chọn file PDF, DOCX hoặc TXT trước.');
      return;
    }
    setParsingAlternative(true);
    setImportError('');
    setImportNote('');
    try {
      const data = new FormData();
      data.append('file', jdFile);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/jobs/parse-file`, data, { headers: { Authorization: `Bearer ${token}` } });
      applyDraft(response.data || {});
    } catch (err) {
      setImportError(getErrorMessage(err, 'Không đọc được file JD. Hãy thử dán nội dung hoặc dùng file PDF/DOCX/TXT khác.'));
    } finally {
      setParsingAlternative(false);
    }
  };

  const parsePastedJd = async () => {
    if (pastedJd.trim().length < 30) {
      setImportError('Hãy dán nội dung mô tả công việc đầy đủ (ít nhất 30 ký tự).');
      return;
    }
    setParsingAlternative(true);
    setImportError('');
    setImportNote('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/jobs/parse-text`, { text: pastedJd }, { headers: { Authorization: `Bearer ${token}` } });
      applyDraft(response.data || {});
    } catch (err) {
      setImportError(getErrorMessage(err, 'Không phân tích được nội dung JD đã dán.'));
    } finally {
      setParsingAlternative(false);
    }
  };

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

  if (loading) return <LoadingState label="Đang tải vị trí tuyển dụng..." />;
  return (
    <div className="jobs-page">
      <div className="page-heading">
        <div><div className="eyebrow">QUẢN LÝ TUYỂN DỤNG</div><h1 className="page-title">{editing ? 'Chỉnh sửa vị trí tuyển dụng' : 'Vị trí tuyển dụng'}</h1><p className="muted">Tạo, cập nhật và theo dõi các vị trí đang tuyển.</p></div>
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      {notice ? <div className="success-box">{notice}</div> : null}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>{editing ? 'Cập nhật vị trí tuyển dụng' : 'Tạo vị trí tuyển dụng'}</h3>
        {!editing ? <section className="jd-import-panel" aria-label="Nhập mô tả công việc">
          <div>
            <strong>Nhập mô tả công việc</strong>
            <p className="muted">Hỗ trợ trang có API tuyển dụng công khai, một số trang HTML, hoặc dùng file và văn bản khi website không cho đọc tự động.</p>
          </div>
          <div className="jd-import-controls">
            <input className="input" type="url" value={sourceUrl} placeholder="https://example.com/jobs/position" aria-label="Đường dẫn tin tuyển dụng" onChange={(event) => setSourceUrl(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); importJobDescription(); } }} />
            <button className="ghost-button" type="button" onClick={importJobDescription} disabled={importing}>{importing ? <><span className="button-spinner button-spinner-muted" aria-hidden="true" />Đang đọc trang...</> : 'Trích xuất JD'}</button>
          </div>
          {availablePostings.length ? <div className="jd-import-controls">
            <select className="input" value={selectedPosting} aria-label="Chọn tin tuyển dụng" onChange={(event) => setSelectedPosting(event.target.value)}>
              {availablePostings.map((posting, index) => <option key={`${posting.title}-${index}`} value={index}>{posting.title}{posting.location ? ` · ${posting.location}` : ''}</option>)}
            </select>
            <button className="primary-button" type="button" onClick={selectPosting}>Dùng tin đã chọn</button>
          </div> : null}
          <div className="jd-import-fallbacks">
            <div className="jd-import-method">
              <strong>Tải file JD</strong>
              <p className="muted">PDF, DOCX hoặc TXT · tối đa 5 MB</p>
              <input className="input" type="file" accept=".pdf,.docx,.txt" aria-label="Chọn file JD" onChange={(event) => setJdFile(event.target.files?.[0] || null)} />
              <button className="ghost-button" type="button" onClick={parseJdFile} disabled={parsingAlternative || !jdFile}>{parsingAlternative ? <><span className="button-spinner button-spinner-muted" aria-hidden="true" />Đang trích xuất...</> : 'Trích xuất file'}</button>
            </div>
            <div className="jd-import-method">
              <strong>Dán nội dung JD</strong>
              <p className="muted">Sao chép phần mô tả từ bất kỳ trang tuyển dụng nào.</p>
              <textarea className="input" rows={3} maxLength={60000} value={pastedJd} placeholder="Dán mô tả công việc tại đây..." onChange={(event) => setPastedJd(event.target.value)} />
              <button className="ghost-button" type="button" onClick={parsePastedJd} disabled={parsingAlternative || pastedJd.trim().length < 30}>{parsingAlternative ? <><span className="button-spinner button-spinner-muted" aria-hidden="true" />Đang phân tích...</> : 'Phân tích văn bản'}</button>
            </div>
          </div>
          {importError ? <div className="error-box" role="alert">{importError}</div> : null}
          {importNote ? <div className="success-box" role="status">{importNote}</div> : null}
          {form.source_url ? <div className="muted">Nguồn được lưu cùng vị trí: <a href={form.source_url} target="_blank" rel="noreferrer">{form.source_url}</a></div> : null}
        </section> : form.source_url ? <div className="notice-box" style={{ marginBottom: 16 }}>Nguồn mô tả công việc: <a href={form.source_url} target="_blank" rel="noreferrer">{form.source_url}</a></div> : null}
        <form className="form-grid" onSubmit={handleSubmit}>
          <h4>Thông tin vị trí</h4>
          <div className="form-row"><input className="input" name="title" value={form.title} placeholder="Tên vị trí" minLength={2} required onChange={(e) => setField('title', e.target.value)} /><input className="input" name="company_name" value={form.company_name} placeholder="Tên công ty" onChange={(e) => setField('company_name', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="department" value={form.department} placeholder="Phòng ban" onChange={(e) => setField('department', e.target.value)} /><input className="input" name="location" value={form.location} placeholder="Địa điểm" onChange={(e) => setField('location', e.target.value)} /></div>
          <div className="form-row"><input className="input" name="employment_type" value={form.employment_type} placeholder="Hình thức làm việc" onChange={(e) => setField('employment_type', e.target.value)} /><input className="input" name="salary" value={form.salary} placeholder="Mức lương" onChange={(e) => setField('salary', e.target.value)} /></div>
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
          <div className="page-actions"><Link className="ghost-button" to={editing ? `/jobs/${jobId}` : '/jobs'}>Hủy</Link><button className="primary-button" type="submit" disabled={submitting}>{submitting ? <><span className="button-spinner" aria-hidden="true" />Đang lưu...</> : 'Lưu vị trí tuyển dụng'}</button></div>
        </form>
      </div>
      {!editing ? <div className="card jobs-list-card">
        <div className="section-heading jobs-list-heading">
          <div><h2>Danh sách vị trí</h2><p>{visibleJobs.length} vị trí · {openJobCount} đang tuyển · {closedJobCount} đã đóng</p></div>
          <select className="input" aria-label="Lọc vị trí tuyển dụng" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={{ width: 'auto', minWidth: 190 }}>
            <option value="open">Đang tuyển ({openJobCount})</option>
            <option value="closed">Đã đóng ({closedJobCount})</option>
            <option value="all">Tất cả vị trí ({jobs.length})</option>
          </select>
        </div>
        <div className="table-wrap"><table className="table"><thead><tr><th>Vị trí</th><th>Công ty</th><th>Phòng ban</th><th>Địa điểm</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{visibleJobs.length ? visibleJobs.map((job) => <tr key={job.id}><td><strong>{job.title}</strong></td><td>{job.company_name || '-'}</td><td>{job.department || '-'}</td><td>{job.location || '-'}</td><td><span className={`status-badge ${job.status === 'open' ? 'status-open' : 'status-closed'}`}>{job.status === 'open' ? 'Đang tuyển' : 'Đã đóng'}</span></td><td><div className="table-actions"><Link className="action-button" to={`/jobs/${job.id}`}>Chi tiết</Link><Link className="action-button" to={`/jobs/${job.id}/edit`}>Chỉnh sửa</Link><Link className="action-button action-button-primary" to={`/jobs/${job.id}/candidates`}>Xếp hạng ứng viên</Link><button className="action-button action-button-danger" type="button" aria-label={`Xóa vị trí ${job.title}`} onClick={() => deleteJob(job)} disabled={deletingJobId === job.id}>{deletingJobId === job.id ? 'Đang xóa…' : 'Xóa vị trí'}</button></div></td></tr>) : <tr><td colSpan="6" className="muted">Không có vị trí trong bộ lọc này.</td></tr>}</tbody></table></div>
      </div> : null}
      <ConfirmDialog
        open={Boolean(jobToDelete)}
        title="Xóa vị trí tuyển dụng?"
        description={jobToDelete ? `Vị trí “${jobToDelete.title}” và các kết quả đánh giá liên quan sẽ bị xóa. Hồ sơ ứng viên và CV vẫn được giữ lại.` : ''}
        busy={Boolean(deletingJobId)}
        onCancel={() => setJobToDelete(null)}
        onConfirm={confirmDeleteJob}
      />
    </div>
  );
}
