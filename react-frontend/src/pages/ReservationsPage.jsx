import React from 'react';
import { Bell, Check, X } from 'lucide-react';
import { post } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function Reservations({ tell, setBusy }) {
  const { data, error, refresh } = useData('/reservations');

  async function change(id, status) {
    setBusy(true);
    try {
      tell((await post(`/reservations/${id}/status`, { status })).message);
      refresh();
    } catch (e) {
      tell(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Header title="Yêu cầu đặt trước" subtitle="Theo dõi và xử lý các lượt độc giả đặt sách." />
      <Panel title="Danh sách yêu cầu">
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={data.items}
            columns={[
              ['reader', 'ĐỘC GIẢ'],
              ['title', 'ĐẦU SÁCH'],
              ['reserved_at', 'NGÀY ĐẶT'],
              ['status', 'TRẠNG THÁI'],
            ]}
            actions={(r) =>
              r.status === 'Chờ xử lý' ? (
                <>
                  <button className="mini success" title="Thông báo" onClick={() => change(r.id, 'Đã thông báo')}>
                    <Bell size={15} />
                  </button>
                  <button className="mini danger" title="Hủy" onClick={() => change(r.id, 'Đã hủy')}>
                    <X size={15} />
                  </button>
                </>
              ) : r.status === 'Đã thông báo' ? (
                <button className="mini success" onClick={() => change(r.id, 'Hoàn tất')}>
                  <Check size={15} />
                </button>
              ) : null
            }
          />
        )}
      </Panel>
    </>
  );
}
