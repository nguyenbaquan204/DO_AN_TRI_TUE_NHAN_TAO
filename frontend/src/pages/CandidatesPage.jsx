import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState(null);

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

  const deleteCandidate = async (candidate) => {
    const confirmed = window.confirm(`Bạn có chắc muốn xóa hồ sơ của ${candidate.full_name}? Các lượt đánh giá và tệp CV liên quan cũng sẽ bị xóa.`);
    if (!confirmed) return;
    setDeletingId(candidate.id);
    setError('');
    setNotice('');
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/candidates/${candidate.id}`, { headers: { Authorization: `Bearer ${token}` } });
      setCandidates((current) => current.filter((item) => item.id !== candidate.id));
      setNotice(`Đã xóa hồ sơ ${candidate.full_name}.`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Không thể xóa hồ sơ ứng viên. Vui lòng thử lại.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <div>Đang tải ứng viên...</div>;

  return (
    <div>
      <div className="page-title">Ứng viên</div>
      {error ? <div className="error-box">{error}</div> : null}
      {notice ? <div className="success-box">{notice}</div> : null}
      <div className="card" style={{ marginBottom: 16 }}><input className="input" placeholder="Tìm theo tên hoặc email" value={search} onChange={(event) => setSearch(event.target.value)} /></div>
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
                  <td>{candidate.analysis_status || '-'}</td>
                  <td><div className="table-actions"><Link className="action-button" to={`/candidates/${candidate.id}`}>Xem hồ sơ</Link><button className="action-button action-button-danger" type="button" onClick={() => deleteCandidate(candidate)} disabled={deletingId === candidate.id}>{deletingId === candidate.id ? 'Đang xóa…' : 'Xóa'}</button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
