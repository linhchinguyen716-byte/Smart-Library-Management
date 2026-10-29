import React, { useState } from 'react';
import { ArrowRight, BookOpen, Search } from 'lucide-react';
import { post } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function ReaderHome({ tell, setBusy }) {
  const { data, error, refresh } = useData('/reader/home');
  const [tab, setTab] = useState('books');
  const [search, setSearch] = useState('');

  async function reserve(id) {
    if (!confirm('Gửi yêu cầu đặt trước sách này?')) return;
    setBusy(true);
    try {
      tell((await post(`/reader/reserve/${id}`)).message);
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
        kicker="KHÔNG GIAN ĐỘC GIẢ"
        title="Thư viện của tôi"
        subtitle="Khám phá kho sách, đặt trước và theo dõi các lượt mượn của bạn."
      />
      <div className="tab-row">
        {[
          ['books', 'Danh mục sách'],
          ['reservations', 'Sách đã đặt'],
          ['loans', 'Lịch sử mượn'],
        ].map(([k, t]) => (
          <button key={k} className={tab === k ? 'current' : ''} onClick={() => setTab(k)}>
            {t}
          </button>
        ))}
      </div>
      <ErrorLine error={error} />
      {!data ? (
        <Loading />
      ) : (
        <Panel
          title={
            tab === 'books'
              ? 'Khám phá kho sách'
              : tab === 'reservations'
              ? 'Yêu cầu đặt trước của tôi'
              : 'Lịch sử mượn sách'
          }
          extra={
            tab === 'books' ? (
              <div className="search">
                <Search size={16} />
                <input
                  placeholder="Tìm sách hoặc tác giả"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            ) : null
          }
        >
          {tab === 'books' ? (
            <div className="book-cards">
              {data.books
                .filter((x) => (x.title + x.author + x.code).toLowerCase().includes(search.toLowerCase()))
                .map((b) => (
                  <div className="book-card" key={b.id}>
                    <div className="book-art">
                      <BookOpen size={38} />
                    </div>
                    <span className="book-code">
                      {b.code} / {b.category || 'CHƯA PHÂN LOẠI'}
                    </span>
                    <h3>{b.title}</h3>
                    <p>{b.author}</p>
                    <div className="book-end">
                      <span>{b.available > 0 ? `Còn ${b.available} cuốn` : 'Tạm hết sách'}</span>
                      <button className="btn small" onClick={() => reserve(b.id)}>
                        Đặt trước <ArrowRight size={14} />
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          ) : tab === 'reservations' ? (
            <Table
              items={data.reservations}
              columns={[
                ['title', 'TÊN SÁCH'],
                ['reserved_at', 'NGÀY ĐẶT'],
                ['status', 'TRẠNG THÁI'],
              ]}
            />
          ) : (
            <Table
              items={data.loans}
              columns={[
                ['code', 'MÃ PHIẾU'],
                ['titles', 'SÁCH ĐÃ MƯỢN'],
                ['borrow_date', 'NGÀY MƯỢN'],
                ['due_date', 'HẠN TRẢ'],
                ['status', 'TRẠNG THÁI'],
              ]}
            />
          )}
        </Panel>
      )}
    </>
  );
}
