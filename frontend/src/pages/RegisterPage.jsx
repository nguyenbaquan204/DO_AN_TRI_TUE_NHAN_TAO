import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { getAuthErrorMessage } from '../utils/authError';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/auth/register`, form);
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (error) {
      setError(getAuthErrorMessage(error, 'Không thể tạo tài khoản. Vui lòng thử lại.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card" aria-labelledby="register-title">
      <div className="auth-brand"><span className="brand-mark">A</span><span><strong>AI Recruit</strong><small>TRỢ LÝ TUYỂN DỤNG</small></span></div>
      <h1 id="register-title">Tạo tài khoản</h1>
      <p className="auth-description">Bắt đầu quản lý vị trí tuyển dụng và hồ sơ ứng viên của bạn.</p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="register-name">Họ tên</label>
          <input id="register-name" className="input" name="name" autoComplete="name" required minLength={2} value={form.name} onChange={handleChange} placeholder="Nguyễn Văn An" />
        </div>
        <div className="form-field">
          <label htmlFor="register-email">Email</label>
          <input id="register-email" className="input" type="email" name="email" autoComplete="email" required value={form.email} onChange={handleChange} placeholder="ten@congty.com" />
        </div>
        <div className="form-field">
          <label htmlFor="register-password">Mật khẩu <span className="label-hint">(ít nhất 8 ký tự)</span></label>
          <input id="register-password" className="input" type="password" name="password" minLength={8} autoComplete="new-password" required value={form.password} onChange={handleChange} placeholder="Tạo mật khẩu" />
        </div>
        {error ? <div className="error-box" role="alert">{error}</div> : null}
        <button className="primary-button" type="submit" disabled={loading}>{loading ? <><span className="button-spinner" aria-hidden="true" />Đang tạo tài khoản...</> : 'Tạo tài khoản nhà tuyển dụng'}</button>
      </form>
      <p className="auth-switch">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p>
    </section>
  );
}
