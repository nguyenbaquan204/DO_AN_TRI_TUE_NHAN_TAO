import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const auth = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

const splitList = (value) => (value || '').split(/[,;\n]/).map((item) => item.trim()).filter(Boolean);

function reviewFields(candidateData = {}) {
  return {
    full_name: candidateData.full_name || '',
    email: candidateData.email || '',
    phone: candidateData.phone || '',
    location: candidateData.location || '',
    linkedin: candidateData.linkedin || '',
    github: candidateData.github || '',
    portfolio: candidateData.portfolio || '',
    experience_years: Number(candidateData.experience_years || 0),
    skills: Array.isArray(candidateData.skills) ? candidateData.skills.join(', ') : '',
    education: candidateData.education || '',
    work_experience: candidateData.work_experience || '',
    projects: Array.isArray(candidateData.projects) ? candidateData.projects.join('\n') : '',
    certificates: Array.isArray(candidateData.certificates) ? candidateData.certificates.join('\n') : '',
    languages: Array.isArray(candidateData.languages) ? candidateData.languages.join(', ') : '',
  };
}

function candidatePayload(fields) {
  return {
    ...fields,
    experience_years: Number(fields.experience_years || 0),
    skills: splitList(fields.skills),
    projects: splitList(fields.projects),
    certificates: splitList(fields.certificates),
    languages: splitList(fields.languages),
  };
}

function statusText(status) {
  return {
    PENDING: 'Đang chờ xử lý',
    ANALYZING: 'Đang đọc CV',
    REVIEW: 'Chờ bạn kiểm tra',
    SAVING: 'Đang lưu hồ sơ',
    SAVED: 'Đã lưu ứng viên',
    FAILED: 'Không đọc được CV',
  }[status] || status;
}

export default function UploadCvPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [files, setFiles] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [screening, setScreening] = useState(false);
  const [screened, setScreened] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!jobId) return;
    const loadJob = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/jobs/${jobId}`, { headers: auth() });
        setJob(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Không thể tải vị trí tuyển dụng.');
      }
    };
    loadJob();
  }, [jobId]);

  const candidateIds = useMemo(
    () => queue.filter((item) => item.status === 'SAVED' && item.candidate_id).map((item) => item.candidate_id),
    [queue],
  );

  const updateQueueItem = (index, updates) => {
    setQueue((items) => items.map((item, itemIndex) => (itemIndex === index ? { ...item, ...updates } : item)));
  };

  const previewOne = async (file, index) => {
    updateQueueItem(index, { status: 'ANALYZING', progress: 18, error: '' });
    try {
      const data = new FormData();
      data.append('file', file);
      const response = await axios.post(`${API_URL}/api/resumes/preview`, data, {
        headers: auth(),
        onUploadProgress: (event) => {
          updateQueueItem(index, { progress: event.total ? Math.min(85, Math.round((event.loaded / event.total) * 85)) : 45 });
        },
      });
      updateQueueItem(index, {
        ...response.data,
        status: 'REVIEW',
        progress: 100,
        review: reviewFields(response.data.candidate_data),
        file_name: file.name,
      });
      return true;
    } catch (err) {
      updateQueueItem(index, {
        status: 'FAILED',
        progress: 100,
        error: err.response?.data?.detail || err.message || 'Không thể phân tích CV.',
      });
      return false;
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!files.length) {
      setError('Vui lòng chọn ít nhất một tệp PDF hoặc DOCX.');
      return;
    }
    setLoading(true);
    setScreened(false);
    setError('');
    setMessage('');
    setQueue(files.map((file) => ({ file, file_name: file.name, status: 'PENDING', progress: 0 })));
    let analyzed = 0;
    for (let index = 0; index < files.length; index += 1) {
      if (await previewOne(files[index], index)) analyzed += 1;
    }
    setMessage(`Đã đọc được ${analyzed}/${files.length} CV. Kiểm tra và xác nhận từng hồ sơ trước khi lưu.`);
    setLoading(false);
  };

  const saveCandidate = async (index) => {
    const item = queue[index];
    if (!item?.file || !item.review) return;
    if (!item.review.full_name.trim()) {
      updateQueueItem(index, { error: 'Vui lòng nhập họ và tên ứng viên.' });
      return;
    }
    updateQueueItem(index, { status: 'SAVING', error: '' });
    setError('');
    setScreened(false);
    try {
      const data = new FormData();
      data.append('file', item.file);
      data.append('candidate_data', JSON.stringify(candidatePayload(item.review)));
      const response = await axios.post(`${API_URL}/api/resumes/upload`, data, { headers: auth() });
      updateQueueItem(index, { ...response.data, status: 'SAVED', progress: 100, review: item.review });
      setMessage(`Đã lưu hồ sơ ${response.data.candidate_name}.`);
    } catch (err) {
      updateQueueItem(index, { status: 'REVIEW', error: err.response?.data?.detail || err.message || 'Không lưu được hồ sơ.' });
    }
  };

  const screenCandidates = async () => {
    if (!candidateIds.length) return;
    setScreening(true);
    setError('');
    try {
      const response = await axios.post(
        `${API_URL}/api/matching/jobs/${jobId}/screen-batch`,
        { candidate_ids: candidateIds },
        { headers: auth() },
      );
      setScreened(true);
      setMessage(`Đã sàng lọc ${response.data.completed} ứng viên cho ${job?.title || 'vị trí này'}.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể sàng lọc ứng viên.');
    } finally {
      setScreening(false);
    }
  };

  const retry = async (index) => previewOne(queue[index].file, index);
  const updateReviewField = (index, key, value) => {
    const current = queue[index]?.review || {};
    updateQueueItem(index, { review: { ...current, [key]: value }, error: '' });
  };

  const textField = (item, index, key, label, { type = 'text', full = false } = {}) => (
    <label className={full ? 'cv-review-field cv-review-field-full' : 'cv-review-field'} key={key}>
      <span>{label}</span>
      <input
        className="input"
        type={type}
        min={type === 'number' ? '0' : undefined}
        max={type === 'number' ? '80' : undefined}
        step={type === 'number' ? '0.1' : undefined}
        value={item.review?.[key] ?? ''}
        onChange={(event) => updateReviewField(index, key, type === 'number' ? event.target.value : event.target.value)}
      />
    </label>
  );

  const textAreaField = (item, index, key, label, hint = '') => (
    <label className="cv-review-field cv-review-field-full" key={key}>
      <span>{label}{hint ? <small>{hint}</small> : null}</span>
      <textarea className="input" rows={key === 'work_experience' ? 5 : 3} value={item.review?.[key] ?? ''} onChange={(event) => updateReviewField(index, key, event.target.value)} />
    </label>
  );

  return (
    <div className="upload-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">HỒ SƠ ỨNG VIÊN</div>
          <h1 className="page-title">{jobId ? 'Tải CV cho vị trí' : 'Tải hồ sơ CV'}</h1>
          <p className="muted">{jobId ? `Đọc hồ sơ cho ${job?.title || 'vị trí tuyển dụng'}, kiểm tra thông tin rồi mới lưu.` : 'Đọc thông tin trong CV, cho phép chỉnh sửa trước khi tạo hồ sơ ứng viên.'}</p>
        </div>
        {jobId ? <Link className="ghost-button" to={`/jobs/${jobId}`}>Chi tiết vị trí</Link> : <Link className="ghost-button" to="/candidates">Danh sách ứng viên</Link>}
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      {message ? <div className="success-box">{message}</div> : null}
      <div className="card upload-card">
        <div className="upload-intro"><span className="upload-symbol" aria-hidden="true">↑</span><div><h2>Thêm hồ sơ CV</h2><p className="muted">PDF hoặc DOCX, tối đa 5 MB mỗi tệp. Hệ thống chỉ tạo hồ sơ sau khi bạn xác nhận.</p></div></div>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label htmlFor="cv-file">Tệp hồ sơ</label>
          <input
            id="cv-file"
            className="input"
            type="file"
            multiple
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            aria-label="Chọn một hoặc nhiều tệp CV PDF hoặc DOCX"
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
          />
          <p className="field-hint">Định dạng hỗ trợ: PDF, DOCX{files.length ? ` · Đã chọn ${files.length} tệp` : ''}</p>
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? <><span className="button-spinner" aria-hidden="true" />Đang đọc CV...</> : 'Đọc CV và kiểm tra thông tin'}
          </button>
        </form>
      </div>
      {queue.length ? (
        <div className="card upload-queue-card">
          <div className="section-heading">
            <div><h2>Kiểm tra hồ sơ đã đọc</h2><p>Thông tin nhận diện có thể sai do mẫu CV hoặc OCR. Hãy rà lại trước khi lưu.</p></div>
            <span className="status-badge">{queue.filter((item) => item.status === 'SAVED').length}/{queue.length} đã lưu</span>
          </div>
          <div className="stack">
            {queue.map((item, index) => (
              <div className="upload-queue-item cv-review-item" key={`${item.file.name}-${index}`}>
                <div className="upload-file-info">
                  <span className={`file-symbol ${item.file.name.toLowerCase().endsWith('.docx') ? 'file-symbol-doc' : ''}`} aria-hidden="true">{item.file.name.toLowerCase().endsWith('.docx') ? 'DOC' : 'PDF'}</span>
                  <div className="upload-file-copy">
                    <div className="cv-review-file-heading"><strong>{item.file.name}</strong><span className={`status-badge ${item.status === 'SAVED' ? 'status-open' : item.status === 'FAILED' ? 'status-closed' : ''}`}>{statusText(item.status)}</span></div>
                    {item.status === 'SAVED' ? <div>Ứng viên: <Link to={`/candidates/${item.candidate_id}`}>{item.candidate_name}</Link></div> : null}
                    {item.error ? <div className="upload-item-error">{item.error}</div> : null}
                    {item.status === 'ANALYZING' || item.status === 'PENDING' || item.status === 'SAVING' ? <div className="progress-bar upload-progress" role="progressbar" aria-label={`Tiến độ ${item.file.name}`} aria-valuenow={item.progress || 0} aria-valuemin="0" aria-valuemax="100"><div className="progress-fill" style={{ width: `${item.progress || 0}%` }} /></div> : null}
                  </div>
                </div>
                <div className="row-actions">
                  {item.status === 'FAILED' ? <button type="button" className="ghost-button" onClick={() => retry(index)} disabled={loading}>Đọc lại</button> : null}
                  <button type="button" className="ghost-button" title="Ẩn tệp khỏi danh sách tiến trình" disabled={item.status === 'SAVED' || item.status === 'SAVING' || loading} onClick={() => setQueue((items) => items.filter((_, itemIndex) => itemIndex !== index))}>Ẩn</button>
                </div>
                {item.status === 'REVIEW' ? (
                  <div className="cv-review-panel">
                    <div className="cv-review-panel-heading"><div><strong>Thông tin nhận diện</strong><p>Chỉnh sửa trực tiếp các mục bên dưới. Mục để trống sẽ được lưu là chưa có thông tin.</p></div><span className="badge">Cần bạn xác nhận</span></div>
                    <div className="cv-review-grid">
                      {textField(item, index, 'full_name', 'Họ và tên')}
                      {textField(item, index, 'email', 'Email')}
                      {textField(item, index, 'phone', 'Số điện thoại')}
                      {textField(item, index, 'location', 'Địa điểm')}
                      {textField(item, index, 'experience_years', 'Số năm kinh nghiệm', { type: 'number' })}
                      {textField(item, index, 'github', 'GitHub')}
                      {textField(item, index, 'linkedin', 'LinkedIn')}
                      {textField(item, index, 'portfolio', 'Portfolio')}
                      {textAreaField(item, index, 'skills', 'Kỹ năng', 'Phân cách bằng dấu phẩy.')}
                      {textAreaField(item, index, 'education', 'Học vấn')}
                      {textAreaField(item, index, 'work_experience', 'Kinh nghiệm làm việc')}
                      {textAreaField(item, index, 'projects', 'Dự án', 'Mỗi mục một dòng.')}
                      {textAreaField(item, index, 'certificates', 'Chứng chỉ', 'Mỗi mục một dòng.')}
                      {textAreaField(item, index, 'languages', 'Ngôn ngữ', 'Phân cách bằng dấu phẩy.')}
                    </div>
                    <details className="cv-raw-preview"><summary>Xem văn bản đọc được từ CV</summary><pre>{item.extracted_text_preview || 'Không có văn bản xem trước.'}{item.extracted_text_truncated ? '\n\n… Phần còn lại của nội dung đã được rút gọn trong bản xem trước.' : ''}</pre></details>
                    <div className="page-actions cv-review-actions">
                      <button type="button" className="primary-button" onClick={() => saveCandidate(index)} disabled={loading || item.status === 'SAVING'}>
                        {item.status === 'SAVING' ? <><span className="button-spinner" aria-hidden="true" />Đang lưu...</> : 'Xác nhận và lưu ứng viên'}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
          <div className="page-actions" style={{ marginTop: 16 }}>
            {jobId ? <button type="button" className="primary-button" onClick={screenCandidates} disabled={screening || !candidateIds.length || loading}>
              {screening ? <><span className="button-spinner" aria-hidden="true" />Đang sàng lọc...</> : `Sàng lọc ${candidateIds.length} ứng viên đã lưu`}
            </button> : null}
            {jobId && screened ? <button type="button" className="primary-button" onClick={() => navigate(`/jobs/${jobId}/candidates`)}>Xem xếp hạng</button> : null}
          </div>
        </div>
      ) : null}
      {!jobId ? <Link className="ghost-button" to="/jobs">Chọn vị trí tuyển dụng để sàng lọc CV</Link> : null}
    </div>
  );
}
