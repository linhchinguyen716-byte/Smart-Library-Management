import React from 'react';
import { useData } from '../hooks/useData';
import { ErrorLine, Header, Loading, Panel, Table } from '../components/ui/Common';

export function Activity() {
  const { data, error } = useData('/activity');

  return (
    <>
      <Header title="Nhật ký hoạt động" subtitle="Theo dõi những thay đổi đã được hệ thống ghi nhận." />
      <Panel title="Lịch sử ghi nhận">
        <ErrorLine error={error} />
        {!data ? (
          <Loading />
        ) : (
          <Table
            items={data.items}
            columns={[
              ['created_at', 'THỜI GIAN'],
              ['employee', 'NGƯỜI THỰC HIỆN'],
              ['action', 'HÀNH ĐỘNG'],
              ['description', 'NỘI DUNG'],
            ]}
          />
        )}
      </Panel>
    </>
  );
}
