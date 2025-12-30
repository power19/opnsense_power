import { useApi } from '../hooks/useApi';

interface PipeStat {
  pipe: string;
  description: string;
  current_bps: number;
  current_formatted: string;
  limit_bps: number;
  limit_formatted: string;
  usage_percent: number;
  packets: number;
  bytes: number;
  dropped: number;
  enabled: boolean;
}

interface ShaperResponse {
  pipes: PipeStat[];
  total: number;
  live_stats_available: boolean;
  ssh_configured: boolean;
  ssh_available: boolean;
  ssh_error: string | null;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(2)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(2)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(2)} KB`;
  return `${bytes} B`;
}

function getUsageColor(percent: number): string {
  if (percent >= 90) return 'bg-red-500';
  if (percent >= 70) return 'bg-yellow-500';
  return 'bg-green-500';
}

function getUsageTextColor(percent: number): string {
  if (percent >= 90) return 'text-red-600 dark:text-red-400';
  if (percent >= 70) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-green-600 dark:text-green-400';
}

export function TrafficShapers() {
  const { data, loading, error } = useApi<ShaperResponse>('/shapers/statistics', 10000);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Traffic Shapers</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Traffic Shapers</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!data?.pipes.length) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Traffic Shapers</h2>
        <div className="text-gray-500">No traffic shapers configured</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">
          Traffic Shapers ({data?.total || 0})
        </h2>
        <div className="flex items-center gap-2 text-xs">
          {data?.ssh_available ? (
            <span className="px-2 py-1 rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              SSH Connected
            </span>
          ) : data?.ssh_configured ? (
            <span className="px-2 py-1 rounded bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" title={data?.ssh_error || 'Connection failed'}>
              SSH Error
            </span>
          ) : (
            <span className="px-2 py-1 rounded bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
              SSH Not Configured
            </span>
          )}
        </div>
      </div>
      <div className="space-y-4">
        {data?.pipes.map((pipe) => (
          <div key={pipe.pipe} className={`border dark:border-gray-700 rounded-lg p-4 ${!pipe.enabled ? 'opacity-50' : ''}`}>
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{pipe.description || `Pipe ${pipe.pipe}`}</span>
                <span className="text-sm text-gray-500">({pipe.limit_formatted})</span>
                {!pipe.enabled && (
                  <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                    Disabled
                  </span>
                )}
              </div>
              <div className={`font-mono font-bold ${getUsageTextColor(pipe.usage_percent)}`}>
                {pipe.current_formatted}
                {pipe.usage_percent > 0 && (
                  <span className="text-sm ml-1">({pipe.usage_percent}%)</span>
                )}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${getUsageColor(pipe.usage_percent)}`}
                style={{ width: `${Math.min(pipe.usage_percent, 100)}%` }}
              />
            </div>

            {/* Stats */}
            <div className="flex justify-between mt-2 text-xs text-gray-500">
              <span>Packets: {pipe.packets.toLocaleString()}</span>
              <span>Traffic: {formatBytes(pipe.bytes || 0)}</span>
              <span className={pipe.dropped > 0 ? 'text-red-500' : ''}>
                Dropped: {pipe.dropped.toLocaleString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
