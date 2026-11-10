import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import LoadingState from '../components/LoadingState';
import ConfirmDialog from '../components/ConfirmDialog';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [candidateToDelete, setCandidateToDelete] = useState(null);

  useEffect(() => {
    const fetchCandidates = async () => {
      const token = localStorage.getItem('token');
      try {
        const response = await axios.get(`${API_URL}/api/candidates`, { headers: { Authorization: `Bearer ${token}` }, params: search ? { search } : {} });
        setCandidates(response.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load candidates');
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, [search]);

  const deleteCandidate = (candidate) => setCandidateToDelete(candidate);

  const confirmDeleteCandidate = async () => {
    if (!candidateToDelete) return;
    setDeletingId(candidateToDelete.id);
    setError('');
    setNotice('');
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/candidates/${candidateToDelete.id}`, { headers: { Authorization: `Bearer ${token}` } });
      setCandidates((current) => current.filter((item) => item.id !== candidateToDelete.id));
      setNotice(`Đã xóa hồ sơ ${candidateToDelete.full_name}.`);
      setCandidateToDelete(null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Không thể xóa hồ sơ ứng viên. Vui lòng thử lại.');
      setCandidateToDelete(null);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <LoadingState label="Đang tải danh sách ứng viên..." />;

  return (
    <div className="candidates-page">
      <div className="page-heading">
        <div><div className="eyebrow">HỒ SƠ ỨNG VIÊN</div><h1 className="page-title">Ứng viên</h1><p className="muted">Tìm kiếm, xem hồ sơ và quản lý các CV đã tiếp nhận.</p></div>
        <Link className="primary-button" to="/upload-cv">+ Tải CV lên</Link>
      </div>
      {error ? <div className="error-box">{error}</div> : null}
      {notice ? <div className="success-box">{notice}</div> : null}
      <div className="card search-panel">
        <div className="search-panel-copy"><strong>Tất cả hồ sơ</strong><span>{candidates.length} ứng viên</span></div>
        <input className="input search-input" aria-label="Tìm ứng viên theo tên hoặc email" placeholder="Tìm theo tên hoặc email..." value={search} onChange={(event) => setSearch(event.target.value)} />
      </div>
      <div className="card">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Họ tên</th><th>Email</th><th>Kỹ năng</th><th>Trạng thái</th><th>Thao tác</th></tr>
            </thead>
            <tbody>
              {candidates.length === 0 ? <tr><td colSpan="5" className="muted">Không tìm thấy ứng viên nào.</td></tr> : candidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td>{candidate.full_name}</td>
                  <td>{candidate.email || '-'}</td>
                  <td>{(candidate.skills || []).join(', ') || '-'}</td>
                  <td><span className={`status-badge ${candidate.analysis_status === 'COMPLETED' ? 'status-open' : ''}`}>{candidate.analysis_status === 'COMPLETED' ? 'Đã phân tích' : candidate.analysis_status === 'FAILED' ? 'Lỗi xử lý' : candidate.analysis_status === 'PROCESSING' ? 'Đang xử lý' : candidate.analysis_status || 'Chưa phân tích'}</span></td>
                  <td><div className="table-actions"><Link className="action-button" to={`/candidates/${candidate.id}`}>Xem hồ sơ</Link><button className="action-button action-button-danger" type="button" aria-label={`Xóa hồ sơ ${candidate.full_name}`} onClick={() => deleteCandidate(candidate)} disabled={deletingId === candidate.id}>{deletingId === candidate.id ? 'Đang xóa…' : 'Xóa hồ sơ'}</button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <ConfirmDialog
        open={Boolean(candidateToDelete)}
        title="Xóa hồ sơ ứng viên?"
        description={candidateToDelete ? `Hồ sơ ${candidateToDelete.full_name}, các lượt đánh giá và tệp CV liên quan sẽ bị xóa.` : ''}
        busy={Boolean(deletingId)}
        onCancel={() => setCandidateToDelete(null)}
        onConfirm={confirmDeleteCandidate}
      />
    </div>
  );
}
