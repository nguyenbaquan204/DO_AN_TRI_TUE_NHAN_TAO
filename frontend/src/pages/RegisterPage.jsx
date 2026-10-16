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
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'linear-gradient(135deg, #eff6ff, #f8fafc)' }}>
      <div className="auth-card">
        <h2 style={{ marginBottom: 8 }}>Tạo tài khoản</h2>
        <p style={{ color: '#64748b', marginBottom: 24 }}>Tham gia nền tảng tuyển dụng</p>
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Họ tên</label>
            <input className="input" name="name" autoComplete="name" required minLength={2} value={form.name} onChange={handleChange} />
          </div>
          <div>
            <label>Email</label>
            <input className="input" type="email" name="email" autoComplete="email" required value={form.email} onChange={handleChange} />
          </div>
          {error ? <div className="error-box">{error}</div> : null}
          <div>
            <label>Mật khẩu (ít nhất 8 ký tự)</label>
            <input className="input" type="password" name="password" minLength={8} autoComplete="new-password" required value={form.password} onChange={handleChange} />
          </div>
          <button className="primary-button" disabled={loading}>{loading ? 'Đang tạo tài khoản...' : 'Tạo tài khoản nhà tuyển dụng'}</button>
        </form>
        <p style={{ marginTop: 16, textAlign: 'center' }}>
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </p>
      </div>
    </div>
  );
}
