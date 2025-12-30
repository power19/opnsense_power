import { useApi } from '../hooks/useApi';

interface Device {
  ip: string;
  mac: string;
  interface: string;
  interface_description: string;
  hostname: string;
  vendor: string;
  expired: boolean;
  permanent: boolean;
}

interface ARPResponse {
  devices: Device[];
  total: number;
}

export function ARPTable() {
  const { data, loading, error } = useApi<ARPResponse>('/arp/table');

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Network Devices (ARP)</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Network Devices (ARP)</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">
        Network Devices ({data?.total || 0})
      </h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b dark:border-gray-700">
              <th className="text-left py-2 px-3">IP Address</th>
              <th className="text-left py-2 px-3">MAC Address</th>
              <th className="text-left py-2 px-3">Hostname</th>
              <th className="text-left py-2 px-3">Vendor</th>
              <th className="text-left py-2 px-3">Interface</th>
            </tr>
          </thead>
          <tbody>
            {data?.devices.map((device, idx) => (
              <tr key={idx} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="py-2 px-3 font-mono">{device.ip}</td>
                <td className="py-2 px-3 font-mono text-xs">{device.mac}</td>
                <td className="py-2 px-3">{device.hostname || '-'}</td>
                <td className="py-2 px-3">
                  <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {device.vendor}
                  </span>
                </td>
                <td className="py-2 px-3">{device.interface_description || device.interface}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
