import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function UploadCvPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [files, setFiles] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [screening, setScreening] = useState(false);
  const [screened, setScreened] = useState(false);
  const [globalResult, setGlobalResult] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!jobId) return;
    const loadJob = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/jobs/${jobId}`, {
          headers: { Authorization: 'Bearer ' + token },
        });
        setJob(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load job');
      }
    };
    loadJob();
  }, [jobId]);

  const candidateIds = useMemo(
    () => queue.filter((item) => item.status === 'COMPLETED' && item.candidate_id).map((item) => item.candidate_id),
    [queue],
  );

  const updateQueueItem = (index, updates) => {
    setQueue((items) => items.map((item, itemIndex) => (itemIndex === index ? { ...item, ...updates } : item)));
  };

  const uploadOne = async (file, index) => {
    const formData = new FormData();
    formData.append(jobId ? 'files' : 'file', file);
    if (jobId) formData.append('job_id', jobId);
    updateQueueItem(index, { status: 'UPLOADING', progress: 10, error: '' });
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/resumes/${jobId ? 'upload-batch' : 'upload'}`, formData, {
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          updateQueueItem(index, { progress: event.total ? Math.round((event.loaded / event.total) * 100) : 50 });
        },
      });
      const result = jobId ? response.data.results?.[0] : response.data;
      if (!result?.success) throw new Error(result?.error || 'Upload failed');
      updateQueueItem(index, {
        ...result,
        status: 'COMPLETED',
        progress: 100,
        candidate_name: result.candidate_name || result.file_name,
      });
      if (!jobId) setGlobalResult(result);
      return result;
    } catch (err) {
      updateQueueItem(index, {
        status: 'FAILED',
        progress: 100,
        error: err.response?.data?.detail || err.message || 'Upload failed',
      });
      return null;
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
    setGlobalResult(null);
    setError('');
    setMessage('');
    setQueue(files.map((file) => ({ file, file_name: file.name, status: 'UPLOADING', progress: 0 })));
    const results = [];
    for (let index = 0; index < files.length; index += 1) {
      results.push(await uploadOne(files[index], index));
    }
    const completed = results.filter(Boolean).length;
    setMessage(`Đã tải và phân tích ${completed}/${files.length} CV cho ${job?.title || 'vị trí này'}.`);
    setLoading(false);
  };

  const screenCandidates = async () => {
    if (!candidateIds.length) return;
    setScreening(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/matching/jobs/${jobId}/screen-batch`,
        { candidate_ids: candidateIds },
        { headers: { Authorization: 'Bearer ' + token } },
      );
      setScreened(true);
      setMessage(`Đã sàng lọc ${response.data.completed} ứng viên cho ${job?.title || 'vị trí này'}.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Candidate screening failed');
    } finally {
      setScreening(false);
    }
  };

  const retry = async (index) => {
    await uploadOne(queue[index].file, index);
  };

  return (
    <div>
      <div className="page-title">{jobId ? `Tải CV ứng viên cho: ${job?.title || 'vị trí tuyển dụng'}` : 'Tải CV'}</div>
      {error ? <div className="error-box">{error}</div> : null}
      {message ? <div className="success-box">{message}</div> : null}
      <div className="card" style={{ maxWidth: 700 }}>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label htmlFor="cv-file">Chọn tệp CV (PDF/DOCX)</label>
          <input
            id="cv-file"
            className="input"
            type="file"
            multiple
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
          />
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Tải CV lên'}
          </button>
        </form>
      </div>
      {queue.length ? (
        <div className="card" style={{ marginTop: 24 }}>
          <h3>Hàng đợi tải CV</h3>
          <div className="stack">
            {queue.map((item, index) => (
              <div className="list-item-row" key={`${item.file.name}-${index}`}>
                <div>
                  <strong>{item.file.name}</strong>
                  <div className="muted">{item.file.type || 'không rõ loại tệp'} · {item.status}</div>
                  {item.candidate_name ? <div>Ứng viên: <Link to={`/candidates/${item.candidate_id}`}>{item.candidate_name}</Link></div> : null}
                  {item.error ? <div className="error-box">{item.error}</div> : null}
                </div>
                <div className="row-actions">
                  {item.status === 'FAILED' ? <button type="button" className="ghost-button" onClick={() => retry(index)}>Thử lại</button> : null}
                  <button type="button" className="ghost-button" onClick={() => setQueue((items) => items.filter((_, itemIndex) => itemIndex !== index))}>Xóa</button>
                </div>
              </div>
            ))}
          </div>
          <div className="page-actions" style={{ marginTop: 16 }}>
            {jobId ? <button type="button" className="primary-button" onClick={screenCandidates} disabled={screening || !candidateIds.length || loading}>
              {screening ? 'Đang sàng lọc...' : 'Sàng lọc ứng viên'}
            </button> : null}
            {jobId && screened ? <button type="button" className="primary-button" onClick={() => navigate(`/jobs/${jobId}/candidates`)}>Xem xếp hạng</button> : null}
          </div>
        </div>
      ) : null}
      {globalResult ? (
        <div className="card" style={{ marginTop: 24 }}>
          <h3>Tóm tắt tải lên</h3>
          <div><strong>Mã ứng viên:</strong> {globalResult.candidate_id}</div>
          <div><strong>Resume ID:</strong> {globalResult.resume_id}</div>
          <Link className="primary-button" to={`/candidates/${globalResult.candidate_id}`}>Mở hồ sơ ứng viên</Link>
        </div>
      ) : null}
      {!jobId ? <Link className="ghost-button" to="/jobs">Chọn vị trí tuyển dụng để sàng lọc CV</Link> : null}
    </div>
  );
}
