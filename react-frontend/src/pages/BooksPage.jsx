import React, { useState } from 'react';
import { Pencil, Plus, Search, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Modal, Panel, Table } from '../components/ui/Common';

export function Books({ tell, setBusy }) {
  const { data, error, refresh } = useData('/books');
  const cats = useData('/categories').data?.items || [];
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);

  async function save(form) {
    setBusy(true);
    try {
      const payload = { ...form, quantity: parseInt(form.quantity || 1, 10) };
      const result = await api(modal?.id ? `/books/${modal.id}` : '/books', {
        method: modal?.id ? 'PUT' : 'POST',
        body: payload,
      });
      tell(result.message);
      setModal(null);
      refresh();
    } catch (e) {
      tell(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function del(id) {
    if (!confirm('Xóa sách này?')) return;
    try {
      tell((await api(`/books/${id}`, { method: 'DELETE' })).message);
      refresh();
    } catch (e) {
      tell(e.message);
    }
  }

  const fields = [
    ['code', 'Mã sách'],
    ['title', 'Tên sách'],
    ['author', 'Tác giả'],
    ['publisher', 'Nhà xuất bản'],
    ['year', 'Năm xuất bản', 'number'],
    ['quantity', 'Số lượng', 'number'],
    ['category_id', 'Thể loại', 'select', cats],
  ];

  const filtered = (data?.items || []).filter((x) =>
    [x.code, x.title, x.author, x.category].join(' ').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <Header
        kicker="QUẢN LÝ TÀI NGUYÊN"
        title="Kho sách thư viện"
        subtitle="Tra cứu, thêm mới, cập nhật và kiểm soát số lượng sách."
        action={
          <button className="btn" onClick={() => setModal({ quantity: 1 })}>
            <Plus size={16} /> Thêm sách mới
          </button>
        }
      />
      <Panel
        title="Danh mục ấn phẩm"
        extra={
          <div className="search">
            <Search size={17} />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm mã sách, tên, tác giả…" />
          </div>
        }
      >
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={filtered}
            columns={[
              ['code', 'MÃ SÁCH'],
              ['title', 'TÊN SÁCH'],
              ['author', 'TÁC GIẢ'],
              ['category', 'THỂ LOẠI'],
              ['quantity', 'TỔNG'],
              ['available', 'CÒN'],
            ]}
            actions={(row) => (
              <>
                <button className="mini" onClick={() => setModal(row)} title="Sửa">
                  <Pencil size={15} />
                </button>
                <button className="mini danger" onClick={() => del(row.id)} title="Xóa">
                  <Trash2 size={15} />
                </button>
              </>
            )}
          />
        )}
      </Panel>
      {modal && (
        <Modal
          title={modal.id ? 'Cập nhật sách' : 'Tiếp nhận sách mới'}
          fields={fields}
          initial={modal}
          onClose={() => setModal(null)}
          onSave={save}
        />
      )}
    </>
  );
}
