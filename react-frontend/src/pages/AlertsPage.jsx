import React from 'react';
import { Check } from 'lucide-react';
import { post } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function Alerts({ tell, setBusy }) {
  const { data, error, refresh } = useData('/alerts');

  async function mark(id) {
    setBusy(true);
    try {
      tell((await post(`/alerts/${id}/mark`, { note: 'Đã liên hệ thủ công' })).message);
      refresh();
    } catch (e) {
      tell(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Header
        title="Cảnh báo & nhắc hạn"
        subtitle="Các phiếu đang mượn, sắp đến hạn trong ba ngày hoặc đã quá hạn."
      />
      <Panel title="Phiếu cần nhắc hạn">
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={data.items}
            columns={[
              ['code', 'MÃ PHIẾU'],
              ['reader', 'ĐỘC GIẢ'],
              ['phone', 'ĐIỆN THOẠI'],
              ['due_date', 'HẠN TRẢ'],
            ]}
            actions={(r) => (
              <button className="btn small" onClick={() => mark(r.id)}>
                <Check size={14} /> Ghi nhận nhắc
              </button>
            )}
          />
        )}
      </Panel>
      <p className="helper">Chức năng chỉ ghi nhận nhắc hạn, chưa tự động gửi email hoặc SMS.</p>
    </>
  );
}
