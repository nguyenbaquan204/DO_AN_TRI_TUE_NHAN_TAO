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
    <section className="auth-card" aria-labelledby="login-title">
      <div className="auth-brand"><span className="brand-mark">A</span><span><strong>AI Recruit</strong><small>TRỢ LÝ TUYỂN DỤNG</small></span></div>
      <h1 id="login-title">Chào mừng trở lại</h1>
      <p className="auth-description">Đăng nhập để tiếp tục quản lý vị trí và hồ sơ ứng viên.</p>
      {sessionExpired ? <div className="notice-box" role="status">Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại để tiếp tục.</div> : null}
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="login-email">Email</label>
          <input id="login-email" className="input" type="email" name="email" autoComplete="email" required value={form.email} onChange={handleChange} placeholder="ten@congty.com" />
        </div>
        <div className="form-field">
          <label htmlFor="login-password">Mật khẩu</label>
          <input id="login-password" className="input" type="password" name="password" autoComplete="current-password" required value={form.password} onChange={handleChange} placeholder="Nhập mật khẩu" />
        </div>
        {error ? <div className="error-box" role="alert">{error}</div> : null}
        <button className="primary-button" type="submit" disabled={loading}>{loading ? <><span className="button-spinner" aria-hidden="true" />Đang đăng nhập...</> : 'Đăng nhập'}</button>
      </form>
      <p className="auth-switch">Chưa có tài khoản? <Link to="/register">Tạo tài khoản nhà tuyển dụng</Link></p>
    </section>
  );
}
