import axios from 'axios';

let redirectingToLogin = false;

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login' && !redirectingToLogin) {
        redirectingToLogin = true;
        window.location.replace('/login?reason=session-expired');
      }
    }
    return Promise.reject(error);
  },
);
