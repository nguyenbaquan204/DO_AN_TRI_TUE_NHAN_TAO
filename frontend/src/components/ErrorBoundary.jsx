import { Component } from 'react';
import { Link } from 'react-router-dom';

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error('Frontend rendering error:', error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="card error-state">
        <h2>Đã xảy ra lỗi</h2>
        <p>Không thể hiển thị trang này. Bạn có thể thử lại hoặc quay về vị trí tuyển dụng.</p>
        <div className="page-actions">
          <button className="primary-button" onClick={() => this.setState({ hasError: false })}>Thử lại</button>
          <button className="ghost-button" onClick={() => window.history.back()}>Quay về trang trước</button>
          <Link className="ghost-button" to="/jobs">Về trang Vị trí tuyển dụng</Link>
        </div>
      </div>
    );
  }
}
