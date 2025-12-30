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
  dropped: number;
}

interface ShaperResponse {
  pipes: PipeStat[];
  total: number;
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
      <h2 className="text-lg font-semibold mb-4">
        Traffic Shapers ({data?.total || 0})
      </h2>
      <div className="space-y-4">
        {data?.pipes.map((pipe) => (
          <div key={pipe.pipe} className="border dark:border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <div>
                <span className="font-semibold">{pipe.description || `Pipe ${pipe.pipe}`}</span>
                <span className="text-sm text-gray-500 ml-2">({pipe.limit_formatted})</span>
              </div>
              <div className={`font-mono font-bold ${getUsageTextColor(pipe.usage_percent)}`}>
                {pipe.current_formatted}
                <span className="text-sm ml-1">({pipe.usage_percent}%)</span>
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
