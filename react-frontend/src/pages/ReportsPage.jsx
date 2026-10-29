import React from 'react';
import { useData } from '../hooks/useData';
import { Bars, ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function Reports() {
  const { data, error } = useData('/reports');

  return (
    <>
      <Header title="Báo cáo thống kê" subtitle="Phân tích dữ liệu đầu sách và hoạt động mượn trả." />
      <ErrorLine error={error} />
      {!data ? (
        <Loading />
      ) : (
        <div className="reports-grid">
          <Panel title="Số lượng theo thể loại">
            <Bars items={data.categories} label="name" val="total" />
          </Panel>
          <Panel title="Số phiếu mượn theo tháng">
            <Bars items={data.monthly} label="month" val="total" />
          </Panel>
          <div className="report-full">
            <Panel title="Sách được mượn nhiều">
              <Table
                items={data.popular}
                columns={[
                  ['title', 'TÊN SÁCH'],
                  ['total', 'SỐ LƯỢT MƯỢN'],
                ]}
              />
            </Panel>
          </div>
        </div>
      )}
    </>
  );
}
