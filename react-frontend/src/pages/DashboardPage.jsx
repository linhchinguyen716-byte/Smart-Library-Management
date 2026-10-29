import React from 'react';
import { Bell, BookCopy, BookOpen, CalendarClock, ClipboardList, Users } from 'lucide-react';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function Dashboard() {
  const { data, error } = useData('/dashboard');
  const s = data?.stats || {};
  const metrics = [
    ['Đầu sách', s.books, BookOpen],
    ['Tổng bản sách', s.copies, BookCopy],
    ['Độc giả', s.readers, Users],
    ['Phiếu đang mượn', s.active_loans, ClipboardList],
    ['Sách quá hạn', s.overdue, Bell],
    ['Đơn đặt trước', s.reservations, CalendarClock],
  ];

  return (
    <>
      <Header
        kicker="TỔNG QUAN"
        title="Bảng điều khiển"
        subtitle="Tổng quan tình hình vận hành thư viện và các chỉ số cập nhật từ SQLite."
      />
      <ErrorLine error={error} />
      {!data ? (
        <Loading />
      ) : (
        <>
          <div className="metric-grid">
            {metrics.map(([label, num, Icon], i) => (
              <div className="metric" key={label}>
                <div className="metric-head">
                  <span>{String(i + 1).padStart(2, '0')} / CHỈ SỐ</span>
                  <Icon size={18} />
                </div>
                <strong>{num ?? 0}</strong>
                <p>{label}</p>
              </div>
            ))}
          </div>
          <Panel title="Đầu sách được mượn nhiều" caption="Thống kê từ phiếu mượn thực tế">
            <Table
              items={data.popular}
              columns={[
                ['title', 'TÊN SÁCH'],
                ['borrowed', 'LƯỢT MƯỢN'],
              ]}
              empty="Chưa có lịch sử mượn sách."
            />
          </Panel>
        </>
      )}
    </>
  );
}
