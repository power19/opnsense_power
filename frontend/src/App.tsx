import { useState } from 'react';
import { DHCPLeases } from './components/DHCPLeases';
import { ARPTable } from './components/ARPTable';
import { VLANList } from './components/VLANList';
import { InterfaceStats } from './components/InterfaceStats';
import { TrafficShapers } from './components/TrafficShapers';
import { InterfaceBandwidth } from './components/InterfaceBandwidth';

type Tab = 'dashboard' | 'bandwidth' | 'dhcp' | 'arp' | 'vlans' | 'interfaces' | 'shapers';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const tabs: { id: Tab; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'bandwidth', label: 'Bandwidth' },
    { id: 'dhcp', label: 'DHCP Leases' },
    { id: 'arp', label: 'Network Devices' },
    { id: 'vlans', label: 'VLANs' },
    { id: 'interfaces', label: 'Interfaces' },
    { id: 'shapers', label: 'Traffic Shapers' },
  ];

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-orange-600">OPNsense Monitor</h1>
            <span className="text-sm text-gray-500">Auto-refresh: 10s</span>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'text-orange-600 border-b-2 border-orange-600'
                    : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <InterfaceBandwidth />
              <TrafficShapers />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DHCPLeases />
              <ARPTable />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <VLANList />
              <InterfaceStats />
            </div>
          </div>
        )}
        {activeTab === 'bandwidth' && <InterfaceBandwidth compact />}
        {activeTab === 'dhcp' && <DHCPLeases />}
        {activeTab === 'arp' && <ARPTable />}
        {activeTab === 'vlans' && <VLANList />}
        {activeTab === 'interfaces' && <InterfaceStats />}
        {activeTab === 'shapers' && <TrafficShapers />}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t dark:border-gray-700 mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          OPNsense Monitor - Real-time network monitoring
        </div>
      </footer>
    </div>
  );
}

export default App;
