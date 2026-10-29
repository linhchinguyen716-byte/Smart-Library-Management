import React, { useState } from 'react';
import { ArrowRight, Library, ShieldCheck, UserRound } from 'lucide-react';
import { post } from '../services/api';
import { Field } from '../components/ui/Common';

export function Auth({ onLogin, tell, notice }) {
  const [kind, setKind] = useState('admin');
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const change = (k, v) => setForm((x) => ({ ...x, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (register) {
        await post('/auth/register', form);
        setRegister(false);
        setForm({});
        tell('Đăng ký thành công. Hãy đăng nhập.');
      } else {
        const data = await post('/auth/login', { ...form, kind });
        onLogin(data.user);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-top">
        <Library size={28} /> <strong>SMART LIBRARY</strong>
        <span> / QUẢN LÝ THƯ VIỆN</span>
      </div>
      <div className="auth-card">
        <div className="auth-story">
          <div>
            <div className="eyebrow orange">CỔNG THÔNG TIN THƯ VIỆN</div>
            <h1>
              Hệ thống Quản lý
              <br />
              Thư viện Thông minh
            </h1>
            <p>
              Tra cứu ấn phẩm, quản lý mượn trả và đối soát lưu thông tập trung dành cho cán bộ quản lý và độc giả.
            </p>
          </div>
          <div className="story-footer">
            <span>SMART LIBRARY</span>
            <span>FLASK + REACT + SQLITE</span>
          </div>
        </div>
        <div className="auth-form">
          <div className="eyebrow">{register ? 'ĐĂNG KÝ ĐỘC GIẢ' : 'ĐĂNG NHẬP HỆ THỐNG'}</div>
          <h2>{register ? 'Tạo tài khoản độc giả' : 'Truy cập tài khoản'}</h2>
          <p>Nhập thông tin xác thực để bắt đầu phiên làm việc.</p>
          {!register && (
            <div className="auth-tabs">
              <button
                className={kind === 'admin' ? 'selected' : ''}
                onClick={() => {
                  setKind('admin');
                  setError('');
                }}
              >
                <ShieldCheck size={16} /> Admin / Nhân viên
              </button>
              <button
                className={kind === 'reader' ? 'selected' : ''}
                onClick={() => {
                  setKind('reader');
                  setError('');
                }}
              >
                <UserRound size={16} /> Độc giả
              </button>
            </div>
          )}
          {(error || notice) && <div className={'form-alert ' + (error ? 'bad' : '')}>{error || notice}</div>}
          <form onSubmit={submit}>
            {register && <Field field={['name', 'Họ tên']} value={form.name} onChange={change} />}
            <Field field={['username', 'Tên đăng nhập']} value={form.username} onChange={change} />
            <Field field={['password', 'Mật khẩu', 'password']} value={form.password} onChange={change} />
            {register && (
              <>
                <Field field={['email', 'Email']} value={form.email} onChange={change} />
                <Field field={['phone', 'Số điện thoại']} value={form.phone} onChange={change} />
              </>
            )}
            <button className="btn full" disabled={loading}>
              {loading ? 'Đang xử lý…' : register ? 'Đăng ký tài khoản' : 'Đăng nhập'} <ArrowRight size={17} />
            </button>
          </form>
          <div className="auth-switch">
            {register ? (
              <p>
                Đã có tài khoản?{' '}
                <button type="button" onClick={() => setRegister(false)}>
                  Đăng nhập
                </button>
              </p>
            ) : (
              <p>
                Độc giả mới chưa có tài khoản?{' '}
                <button type="button" onClick={() => setRegister(true)}>
                  Đăng ký ngay
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
