import React, { useState } from 'react';
import { Check, Plus, RotateCcw } from 'lucide-react';
import { post } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Modal, Panel, Table } from '../components/ui/Common';

export function Loans({ tell, setBusy }) {
  const { data, error, refresh } = useData('/loans');
  const readers = useData('/readers').data?.items || [];
  const books = useData('/books').data?.items?.filter((b) => b.available > 0) || [];
  const [modal, setModal] = useState(false);

  async function run(path) {
    setBusy(true);
    try {
      tell((await post(path)).message);
      refresh();
    } catch (e) {
      tell(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function save(form) {
    setBusy(true);
    try {
      tell((await post('/loans', form)).message);
      setModal(false);
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
        title="Mượn và trả sách"
        subtitle="Lập phiếu mới, cập nhật trả sách và gia hạn thời gian mượn."
        action={
          <button className="btn" onClick={() => setModal(true)}>
            <Plus size={16} /> Lập phiếu mượn
          </button>
        }
      />
      <Panel title="Danh sách phiếu mượn">
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={data.items}
            columns={[
              ['code', 'MÃ PHIẾU'],
              ['reader', 'ĐỘC GIẢ'],
              ['books', 'SÁCH MƯỢN'],
              ['due_date', 'HẠN TRẢ'],
              ['status', 'TRẠNG THÁI'],
            ]}
            actions={(row) =>
              row.status === 'Đang mượn' ? (
                <>
                  <button className="mini" onClick={() => run(`/loans/${row.id}/renew`)} title="Gia hạn">
                    <RotateCcw size={15} />
                  </button>
                  <button className="mini success" onClick={() => run(`/loans/${row.id}/return`)} title="Xác nhận đã trả">
                    <Check size={15} />
                  </button>
                </>
              ) : null
            }
          />
        )}
      </Panel>
      {modal && (
        <Modal
          title="Tạo phiếu mượn"
          fields={[
            ['reader_id', 'Độc giả', 'select', readers.map((r) => ({ id: r.id, name: `${r.code} · ${r.name}` }))],
            ['book_id', 'Chọn sách', 'select', books.map((b) => ({ id: b.id, name: `${b.code} · ${b.title} (còn ${b.available})` }))],
            ['quantity', 'Số lượng', 'number'],
            ['due_date', 'Hạn trả', 'date'],
          ]}
          initial={{ quantity: 1 }}
          onClose={() => setModal(false)}
          onSave={save}
        />
      )}
    </>
  );
}
