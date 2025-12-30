import { useApi } from '../hooks/useApi';

interface InterfaceBW {
  name: string;
  rx_bps: number;
  tx_bps: number;
  rx_formatted: string;
  tx_formatted: string;
  total_bps: number;
  total_formatted: string;
  bytes_received: number;
  bytes_transmitted: number;
  bytes_received_formatted: string;
  bytes_transmitted_formatted: string;
}

interface BandwidthResponse {
  interfaces: InterfaceBW[];
  total: number;
  sample_interval: number | null;
}

interface Props {
  compact?: boolean;
}

export function InterfaceBandwidth({ compact = false }: Props) {
  // Poll every 2 seconds for smoother updates
  const { data, loading, error } = useApi<BandwidthResponse>('/interfaces/bandwidth', 2000);

  if (loading && !data) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Interface Bandwidth</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Interface Bandwidth</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  const interfaces = data?.interfaces || [];

  // Compact table view
  if (compact) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">
            Real-Time Bandwidth ({interfaces.length})
          </h2>
          {data?.sample_interval ? (
            <span className="text-xs text-green-600 dark:text-green-400">
              Live - {data.sample_interval.toFixed(1)}s interval
            </span>
          ) : (
            <span className="text-xs text-yellow-600 dark:text-yellow-400">
              Collecting first sample...
            </span>
          )}
        </div>

        {interfaces.length === 0 ? (
          <div className="text-gray-500 text-sm">No interfaces found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b dark:border-gray-700 text-left text-gray-500">
                  <th className="pb-2 font-medium">Interface</th>
                  <th className="pb-2 font-medium text-right">RX</th>
                  <th className="pb-2 font-medium text-right">TX</th>
                  <th className="pb-2 font-medium text-right">Total</th>
                  <th className="pb-2 font-medium text-right">RX Total</th>
                  <th className="pb-2 font-medium text-right">TX Total</th>
                </tr>
              </thead>
              <tbody>
                {interfaces.map((iface) => (
                  <tr key={iface.name} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="py-2 font-mono font-semibold">{iface.name}</td>
                    <td className="py-2 text-right font-mono text-blue-600 dark:text-blue-400">
                      {iface.rx_formatted}
                    </td>
                    <td className="py-2 text-right font-mono text-green-600 dark:text-green-400">
                      {iface.tx_formatted}
                    </td>
                    <td className="py-2 text-right font-mono font-bold">
                      {iface.total_formatted}
                    </td>
                    <td className="py-2 text-right font-mono text-gray-500">
                      {iface.bytes_received_formatted}
                    </td>
                    <td className="py-2 text-right font-mono text-gray-500">
                      {iface.bytes_transmitted_formatted}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  // Card view for dashboard
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">
          Real-Time Bandwidth ({interfaces.length})
        </h2>
        {data?.sample_interval ? (
          <span className="text-xs text-green-600 dark:text-green-400">
            Live - {data.sample_interval.toFixed(1)}s interval
          </span>
        ) : (
          <span className="text-xs text-yellow-600 dark:text-yellow-400">
            Collecting first sample...
          </span>
        )}
      </div>

      {interfaces.length === 0 ? (
        <div className="text-gray-500 text-sm">No interfaces found</div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {interfaces.slice(0, 8).map((iface) => (
            <div key={iface.name} className="border dark:border-gray-700 rounded-lg p-3">
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm font-semibold">{iface.name}</span>
                <span className="font-mono text-sm font-bold text-green-600 dark:text-green-400">
                  {iface.total_formatted}
                </span>
              </div>

              {/* RX/TX bars */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs w-8 text-gray-500">RX</span>
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300 bg-blue-500"
                      style={{
                        width: `${Math.min(100, (iface.rx_bps / Math.max(iface.rx_bps, iface.tx_bps, 1)) * 100)}%`,
                        minWidth: iface.rx_bps > 0 ? '2px' : '0'
                      }}
                    />
                  </div>
                  <span className="text-xs font-mono w-20 text-right">{iface.rx_formatted}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs w-8 text-gray-500">TX</span>
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300 bg-green-500"
                      style={{
                        width: `${Math.min(100, (iface.tx_bps / Math.max(iface.rx_bps, iface.tx_bps, 1)) * 100)}%`,
                        minWidth: iface.tx_bps > 0 ? '2px' : '0'
                      }}
                    />
                  </div>
                  <span className="text-xs font-mono w-20 text-right">{iface.tx_formatted}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
