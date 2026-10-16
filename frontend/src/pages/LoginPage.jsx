import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { getAuthErrorMessage } from '../utils/authError';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function LoginPage() {
  const navigate = useNavigate();
  const sessionExpired = new URLSearchParams(window.location.search).get('reason') === 'session-expired';
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, form);
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (error) {
      setError(getAuthErrorMessage(error, 'Không thể đăng nhập. Vui lòng kiểm tra lại thông tin.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'linear-gradient(135deg, #eff6ff, #f8fafc)' }}>
      <div className="auth-card">
        <h2 style={{ marginBottom: 8 }}>Đăng nhập</h2>
        <p style={{ color: '#64748b', marginBottom: 24 }}>Trợ lý tuyển dụng AI</p>
        {sessionExpired ? <div className="notice-box">Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại để tiếp tục.</div> : null}
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Email</label>
            <input className="input" type="email" name="email" autoComplete="email" required value={form.email} onChange={handleChange} />
          </div>
          <div>
            <label>Mật khẩu</label>
            <input className="input" type="password" name="password" autoComplete="current-password" required value={form.password} onChange={handleChange} />
          </div>
          {error ? <div className="error-box">{error}</div> : null}
          <button className="primary-button" disabled={loading}>{loading ? 'Đang đăng nhập...' : 'Đăng nhập'}</button>
        </form>
        <p style={{ marginTop: 16, textAlign: 'center' }}>
          Chưa có tài khoản? <Link to="/register">Tạo tài khoản</Link>
        </p>
      </div>
    </div>
  );
}
