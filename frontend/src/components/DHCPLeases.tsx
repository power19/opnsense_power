import { useApi } from '../hooks/useApi';

interface Lease {
  ip: string;
  mac: string;
  hostname: string;
  interface: string;
  status: string;
  starts: string;
  ends: string;
  description: string;
}

interface DHCPResponse {
  leases: Lease[];
  total: number;
}

export function DHCPLeases() {
  const { data, loading, error } = useApi<DHCPResponse>('/dhcp/leases');

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">DHCP Leases</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">DHCP Leases</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">
        DHCP Leases ({data?.total || 0})
      </h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b dark:border-gray-700">
              <th className="text-left py-2 px-3">IP Address</th>
              <th className="text-left py-2 px-3">MAC Address</th>
              <th className="text-left py-2 px-3">Hostname</th>
              <th className="text-left py-2 px-3">Interface</th>
              <th className="text-left py-2 px-3">Status</th>
              <th className="text-left py-2 px-3">Expires</th>
            </tr>
          </thead>
          <tbody>
            {data?.leases.map((lease, idx) => (
              <tr key={idx} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="py-2 px-3 font-mono">{lease.ip}</td>
                <td className="py-2 px-3 font-mono text-xs">{lease.mac}</td>
                <td className="py-2 px-3">{lease.hostname || '-'}</td>
                <td className="py-2 px-3">{lease.interface}</td>
                <td className="py-2 px-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    lease.status === 'online'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                  }`}>
                    {lease.status || 'active'}
                  </span>
                </td>
                <td className="py-2 px-3 text-xs">{lease.ends || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
