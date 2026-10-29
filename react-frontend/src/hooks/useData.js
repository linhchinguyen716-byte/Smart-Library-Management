import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function useData(path, dependencies = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((x) => x + 1);

  useEffect(() => {
    let valid = true;
    setError('');
    api(path)
      .then((d) => {
        if (valid) setData(d);
      })
      .catch((e) => {
        if (valid) setError(e.message);
      });
    return () => {
      valid = false;
    };
  }, [path, version, ...dependencies]);

  return { data, error, refresh };
}
