const fieldNames = {
  name: 'Họ tên',
  email: 'Email',
  password: 'Mật khẩu',
};

export function getAuthErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const field = item.loc?.at(-1);
      const label = fieldNames[field] || field;
      if (item.type === 'value_error.email') return 'Email không đúng định dạng.';
      if (item.type === 'string_too_short' && field === 'password') return 'Mật khẩu cần có ít nhất 8 ký tự.';
      if (item.type === 'string_too_short' && field === 'name') return 'Họ tên cần có ít nhất 2 ký tự.';
      return label ? `${label}: ${item.msg}` : item.msg;
    }).join(' ');
  }

  if (typeof detail === 'string') {
    if (detail === 'Incorrect email or password') return 'Email hoặc mật khẩu không chính xác.';
    return detail;
  }

  if (error.code === 'ERR_NETWORK') {
    return 'Không kết nối được máy chủ. Hãy chạy backend tại cổng 8000 rồi thử lại.';
  }

  return fallback;
}
