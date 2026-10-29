import React, { useEffect, useState } from 'react';
import {
  Bell,
  BookCopy,
  BookOpen,
  CalendarClock,
  ChartColumn,
  ClipboardList,
  History,
  LayoutDashboard,
  Library,
  LoaderCircle,
  LogOut,
  Menu,
  ShieldCheck,
  Tag,
  Users,
  X,
} from 'lucide-react';
import { api, post } from './services/api';
import { Auth } from './pages/AuthPage';
import { Dashboard } from './pages/DashboardPage';
import { Books } from './pages/BooksPage';
import { GenericCrud } from './pages/GenericCrudPage';
import { Loans } from './pages/LoansPage';
import { Reservations } from './pages/ReservationsPage';
import { Alerts } from './pages/AlertsPage';
import { Reports } from './pages/ReportsPage';
import { Activity } from './pages/ActivityPage';
import { ReaderHome } from './pages/ReaderHomePage';

export default function App() {
  const [user, setUser] = useState(undefined);
  const [page, setPage] = useState('dashboard');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [sidebar, setSidebar] = useState(false);

  useEffect(() => {
    api('/session')
      .then((d) => {
        setUser(d.user);
        setPage(d.user?.kind === 'reader' ? 'reader' : 'dashboard');
      })
      .catch(() => setUser(null));
  }, []);

  const tell = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 5000);
  };

  async function logout() {
    await post('/auth/logout');
    setUser(null);
    setPage('dashboard');
    tell('Đã đăng xuất.');
  }

  if (user === undefined) {
    return (
      <div className="center">
        <LoaderCircle className="spin" /> Đang kết nối Flask…
      </div>
    );
  }

  if (!user) {
    return (
      <Auth
        onLogin={(u) => {
          setUser(u);
          setPage(u.kind === 'reader' ? 'reader' : 'dashboard');
        }}
        tell={tell}
        notice={notice}
      />
    );
  }

  const admin = user.kind === 'admin';
  const nav = admin
    ? [
        ['dashboard', 'Tổng quan', LayoutDashboard],
        ['books', 'Kho sách', BookCopy],
        ['categories', 'Thể loại', Tag],
        ['readers', 'Độc giả', Users],
        ['loans', 'Mượn / Trả', ClipboardList],
        ['reservations', 'Đặt trước', CalendarClock],
        ['alerts', 'Cảnh báo', Bell],
        ['reports', 'Thống kê', ChartColumn],
        ['activity', 'Nhật ký', History],
        ...(user.role === 'Admin' ? [['employees', 'Nhân viên', ShieldCheck]] : []),
      ]
    : [['reader', 'Thư viện của tôi', BookOpen]];

  return (
    <div className="app-shell">
      <aside className={'sidebar ' + (sidebar ? 'open' : '')}>
        <div className="brand">
          <div className="brand-icon">
            <Library size={24} />
          </div>
          <div>
            <strong>SMART LIBRARY</strong>
            <small>LIBRARY OPERATIONS / 2026</small>
          </div>
        </div>
        <div className="side-label">KHÔNG GIAN LÀM VIỆC</div>
        <nav>
          {nav.map(([id, label, Icon], i) => (
            <button
              key={id}
              className={'nav-item ' + (page === id ? 'active' : '')}
              onClick={() => {
                setPage(id);
                setSidebar(false);
                setNotice('');
              }}
            >
              <span className="nav-index">{String(i + 1).padStart(2, '0')}</span>
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="identity">
            <div className="avatar">{user.name?.charAt(0)?.toUpperCase()}</div>
            <div>
              <strong>{user.name}</strong>
              <small>{admin ? user.role : 'Độc giả'}</small>
            </div>
          </div>
          <button className="nav-item signout" onClick={logout}>
            <LogOut size={16} /> Đăng xuất
          </button>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setSidebar(!sidebar)}>
            {sidebar ? <X size={20} /> : <Menu size={20} />}
          </button>
          <span className="breadcrumbs">
            SMART LIBRARY <span>/</span> {nav.find((n) => n[0] === page)?.[1] || 'Trang chủ'}
          </span>
          <span className="server-pill">
            <span /> FLASK · ONLINE
          </span>
        </header>
        <main className="content">
          {notice && (
            <div className="notice">
              {notice}
              <button onClick={() => setNotice('')}>×</button>
            </div>
          )}
          {busy && <div className="loading-line" />}
          {page === 'dashboard' && <Dashboard tell={tell} />}
          {page === 'books' && <Books tell={tell} setBusy={setBusy} />}
          {page === 'categories' && (
            <GenericCrud
              title="Phân loại sách"
              subtitle="Các thể loại được lưu trong kho dữ liệu"
              path="/categories"
              fields={[
                ['name', 'Tên thể loại'],
                ['description', 'Mô tả'],
              ]}
              columns={[
                ['name', 'Thể loại'],
                ['description', 'Mô tả'],
              ]}
              tell={tell}
              setBusy={setBusy}
            />
          )}
          {page === 'readers' && (
            <GenericCrud
              title="Danh sách độc giả"
              subtitle="Quản lý hồ sơ người sử dụng thư viện"
              path="/readers"
              fields={[
                ['code', 'Mã độc giả'],
                ['name', 'Họ tên'],
                ['dob', 'Ngày sinh', 'date'],
                ['phone', 'Số điện thoại'],
                ['email', 'Email'],
                ['address', 'Địa chỉ'],
              ]}
              columns={[
                ['code', 'Mã'],
                ['name', 'Tên độc giả'],
                ['phone', 'Số điện thoại'],
                ['email', 'Email'],
              ]}
              tell={tell}
              setBusy={setBusy}
              editable
            />
          )}
          {page === 'employees' && (
            <GenericCrud
              title="Nhân sự thư viện"
              subtitle="Chỉ quản trị viên được xem và tạo nhân viên"
              path="/employees"
              fields={[
                ['code', 'Mã nhân viên'],
                ['name', 'Họ tên'],
                ['username', 'Tên đăng nhập'],
                ['password', 'Mật khẩu', 'password'],
                ['role', 'Vai trò', 'select', ['Nhân viên', 'Admin']],
              ]}
              columns={[
                ['code', 'Mã'],
                ['name', 'Họ tên'],
                ['username', 'Tài khoản'],
                ['role', 'Vai trò'],
              ]}
              tell={tell}
              setBusy={setBusy}
              noDelete
            />
          )}
          {page === 'loans' && <Loans tell={tell} setBusy={setBusy} />}
          {page === 'reservations' && <Reservations tell={tell} setBusy={setBusy} />}
          {page === 'alerts' && <Alerts tell={tell} setBusy={setBusy} />}
          {page === 'reports' && <Reports />}
          {page === 'activity' && <Activity />}
          {page === 'reader' && <ReaderHome tell={tell} setBusy={setBusy} />}
        </main>
      </div>
    </div>
  );
}
