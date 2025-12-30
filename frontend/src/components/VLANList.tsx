import { useApi } from '../hooks/useApi';

interface VLAN {
  uuid: string;
  vlanif: string;
  tag: string;
  device: string;
  description: string;
  pcp: string;
}

interface VLANResponse {
  vlans: VLAN[];
  total: number;
}

export function VLANList() {
  const { data, loading, error } = useApi<VLANResponse>('/vlans/list');

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">VLANs</h2>
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">VLANs</h2>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">
        VLANs ({data?.total || 0})
      </h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b dark:border-gray-700">
              <th className="text-left py-2 px-3">Tag</th>
              <th className="text-left py-2 px-3">Interface</th>
              <th className="text-left py-2 px-3">Parent Device</th>
              <th className="text-left py-2 px-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {data?.vlans.map((vlan) => (
              <tr key={vlan.uuid} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="py-2 px-3">
                  <span className="px-2 py-1 rounded text-xs font-bold bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                    {vlan.tag}
                  </span>
                </td>
                <td className="py-2 px-3 font-mono">{vlan.vlanif}</td>
                <td className="py-2 px-3 font-mono">{vlan.device}</td>
                <td className="py-2 px-3">{vlan.description || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
