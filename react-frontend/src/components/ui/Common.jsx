import React, { useState } from 'react';
import { Archive, ArrowRight, LoaderCircle, X } from 'lucide-react';
import { fmt } from '../../services/api';

export function Header({ kicker, title, subtitle, action }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{kicker || 'QUẢN TRỊ THƯ VIỆN'} / SMART LIBRARY</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </div>
  );
}

export function Panel({ title, caption, children, extra }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {caption && <small>{caption}</small>}
        </div>
        {extra}
      </div>
      {children}
    </section>
  );
}

export function Empty({ text = 'Chưa có dữ liệu.' }) {
  return (
    <div className="empty">
      <Archive size={30} />
      <p>{text}</p>
    </div>
  );
}

export function Loading() {
  return (
    <div className="empty">
      <LoaderCircle className="spin" size={23} />
      <p>Đang tải dữ liệu…</p>
    </div>
  );
}

export function ErrorLine({ error }) {
  return error ? <p className="error-line">{error}</p> : null;
}

export function Table({ columns, items, actions, empty }) {
  if (!items?.length) return <Empty text={empty} />;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map(([k, l]) => (
              <th key={k}>{l}</th>
            ))}
            {actions && <th>THAO TÁC</th>}
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={row.id || i}>
              {columns.map(([key]) => (
                <td key={key}>
                  {key === 'status' ? (
                    <span className={'status ' + (row[key] === 'Đang mượn' || row[key] === 'Chờ xử lý' ? 'warning' : '')}>
                      {fmt(row[key])}
                    </span>
                  ) : (
                    fmt(row[key])
                  )}
                </td>
              ))}
              {actions && (
                <td>
                  <div className="row-actions">{actions(row)}</div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Field({ field, value, onChange }) {
  const [key, label, type, options] = field;
  return (
    <label className="field">
      <span>{label}</span>
      {type === 'select' ? (
        <select value={value ?? ''} onChange={(e) => onChange(key, e.target.value)}>
          <option value="">— Chọn —</option>
          {options?.map((o) => (
            <option key={typeof o === 'string' ? o : o.id} value={typeof o === 'string' ? o : o.id}>
              {typeof o === 'string' ? o : o.name}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={type || 'text'}
          value={value ?? ''}
          onChange={(e) => onChange(key, e.target.value)}
          placeholder={label}
        />
      )}
    </label>
  );
}

export function Modal({ title, fields, initial = {}, onClose, onSave, saving }) {
  const [form, setForm] = useState(initial);
  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSave(form);
          }}
        >
          <div className="form-grid">
            {fields.map((f) => (
              <Field key={f[0]} field={f} value={form[f[0]]} onChange={(k, v) => setForm((x) => ({ ...x, [k]: v }))} />
            ))}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn light" onClick={onClose}>
              Hủy
            </button>
            <button className="btn" disabled={saving}>
              {saving ? 'Đang lưu…' : 'Lưu thông tin'} <ArrowRight size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function Bars({ items = [], label, val }) {
  const max = Math.max(1, ...items.map((x) => Number(x[val] || 0)));
  return items.length ? (
    <div className="bars">
      {items.map((x, i) => (
        <div className="bar-row" key={i}>
          <span>{x[label]}</span>
          <div className="bar-track">
            <div style={{ width: (100 * Number(x[val])) / max + '%' }} />
          </div>
          <strong>{x[val]}</strong>
        </div>
      ))}
    </div>
  ) : (
    <Empty text="Chưa có dữ liệu thống kê." />
  );
}
