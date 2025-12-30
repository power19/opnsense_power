import { useApi } from '../hooks/useApi';

interface InterfaceStat {
  name: string;
  bytes_received: number;
  bytes_transmitted: number;
  bytes_received_formatted: string;
  bytes_transmitted_formatted: string;
  packets_received: number;
  packets_transmitted: number;
  input_errors: number;
  output_errors: number;
  collisions: number;
}

interface InterfaceResponse {
  interfaces: InterfaceStat[];
  total: number;
}

export function InterfaceStats() {
  const { data, loading, error } = useApi<InterfaceResponse>('/interfaces/statistics');

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Interface Statistics</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Interface Statistics</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">
        Interface Statistics ({data?.total || 0})
      </h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b dark:border-gray-700">
              <th className="text-left py-2 px-3">Interface</th>
              <th className="text-right py-2 px-3">RX</th>
              <th className="text-right py-2 px-3">TX</th>
              <th className="text-right py-2 px-3">Packets In</th>
              <th className="text-right py-2 px-3">Packets Out</th>
              <th className="text-right py-2 px-3">Errors</th>
            </tr>
          </thead>
          <tbody>
            {data?.interfaces.map((iface) => (
              <tr key={iface.name} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="py-2 px-3 font-mono font-semibold">{iface.name}</td>
                <td className="py-2 px-3 text-right text-green-600 dark:text-green-400">
                  {iface.bytes_received_formatted}
                </td>
                <td className="py-2 px-3 text-right text-blue-600 dark:text-blue-400">
                  {iface.bytes_transmitted_formatted}
                </td>
                <td className="py-2 px-3 text-right">{iface.packets_received.toLocaleString()}</td>
                <td className="py-2 px-3 text-right">{iface.packets_transmitted.toLocaleString()}</td>
                <td className="py-2 px-3 text-right">
                  {iface.input_errors + iface.output_errors > 0 ? (
                    <span className="text-red-500">{iface.input_errors + iface.output_errors}</span>
                  ) : (
                    <span className="text-gray-400">0</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
