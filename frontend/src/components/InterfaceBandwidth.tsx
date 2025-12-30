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

function getBandwidthColor(bps: number): string {
  if (bps >= 100_000_000) return 'bg-red-500'; // 100+ Mbps
  if (bps >= 50_000_000) return 'bg-orange-500'; // 50+ Mbps
  if (bps >= 10_000_000) return 'bg-yellow-500'; // 10+ Mbps
  if (bps >= 1_000_000) return 'bg-green-500'; // 1+ Mbps
  return 'bg-blue-500';
}

export function InterfaceBandwidth() {
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

  // Filter to only show interfaces with traffic
  const activeInterfaces = data?.interfaces.filter(iface =>
    iface.total_bps > 0 || iface.bytes_received > 0 || iface.bytes_transmitted > 0
  ) || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">
          Real-Time Bandwidth
        </h2>
        {data?.sample_interval && (
          <span className="text-xs text-gray-500">
            Updated every {data.sample_interval.toFixed(1)}s
          </span>
        )}
      </div>

      {activeInterfaces.length === 0 ? (
        <div className="text-gray-500 text-sm">Waiting for traffic data...</div>
      ) : (
        <div className="space-y-3">
          {activeInterfaces.slice(0, 10).map((iface) => (
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
                  <span className="text-xs font-mono w-24 text-right">{iface.rx_formatted}</span>
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
                  <span className="text-xs font-mono w-24 text-right">{iface.tx_formatted}</span>
                </div>
              </div>

              {/* Total bytes */}
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>Total RX: {iface.bytes_received_formatted}</span>
                <span>Total TX: {iface.bytes_transmitted_formatted}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
