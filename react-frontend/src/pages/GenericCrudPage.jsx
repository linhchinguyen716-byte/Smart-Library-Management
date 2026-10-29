import React, { useState } from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Modal, Panel, Table } from '../components/ui/Common';

export function GenericCrud({ title, subtitle, path, fields, columns, tell, setBusy, editable = false, noDelete = false }) {
  const { data, error, refresh } = useData(path);
  const [modal, setModal] = useState(null);

  async function save(form) {
    setBusy(true);
    try {
      const r = await api(path + (modal?.id ? `/${modal.id}` : ''), {
        method: modal?.id ? 'PUT' : 'POST',
        body: form,
      });
      tell(r.message);
      setModal(null);
      refresh();
    } catch (e) {
      tell(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function del(id) {
    if (!confirm('Bạn có chắc muốn xóa?')) return;
    try {
      tell((await api(`${path}/${id}`, { method: 'DELETE' })).message);
      refresh();
    } catch (e) {
      tell(e.message);
    }
  }

  return (
    <>
      <Header
        title={title}
        subtitle={subtitle}
        action={
          <button className="btn" onClick={() => setModal({})}>
            <Plus size={16} /> Thêm mới
          </button>
        }
      />
      <Panel title="Danh sách hiện có">
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={data.items}
            columns={columns}
            actions={
              editable || !noDelete
                ? (row) => (
                    <>
                      {editable && (
                        <button className="mini" onClick={() => setModal(row)}>
                          <Pencil size={16} />
                        </button>
                      )}
                      {!noDelete && (
                        <button className="mini danger" onClick={() => del(row.id)}>
                          <Trash2 size={16} />
                        </button>
                      )}
                    </>
                  )
                : null
            }
          />
        )}
      </Panel>
      {modal && (
        <Modal
          title={modal.id ? 'Sửa thông tin' : 'Thêm bản ghi mới'}
          fields={fields}
          initial={modal}
          onClose={() => setModal(null)}
          onSave={save}
        />
      )}
    </>
  );
}
