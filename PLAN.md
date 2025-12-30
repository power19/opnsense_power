# OPNsense Monitoring Web App - Implementation Plan

## Overview
A simple, real-time web dashboard to monitor OPNsense network infrastructure.

---

## Features to Implement

### 1. **DHCP Leases Dashboard**
- Display all active DHCP leases
- Show: IP address, MAC address, hostname, lease start/end time
- Filter/search by hostname or IP
- API: `/api/dhcpv4/leases/searchLease`

### 2. **VLAN Overview**
- List all configured VLANs
- Show: VLAN ID, description, parent interface, IP assignments
- API: `/api/interfaces/vlan_settings/get`

### 3. **Network Devices (ARP Table)**
- Display all discovered devices on the network
- Show: IP address, MAC address, interface, manufacturer (OUI lookup)
- API: `/api/diagnostics/interface/getArp`

### 4. **Interface Statistics**
- Show all network interfaces with their IPs
- Display real-time traffic (in/out bytes, packets, errors)
- API: `/api/diagnostics/interface/getInterfaceStatistics`

### 5. **Traffic Shaper Status** ⭐ (Key Feature)
- Display all traffic shaper pipes/queues
- Real-time bandwidth usage per shaper
- Show: current usage vs. configured limits
- Visual progress bars for bandwidth consumption
- API: `/api/trafficshaper/settings/get`
- API: `/api/diagnostics/firewall/pfStatistics` (for live stats)

---

## Proposed Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Vite + React + TypeScript                            │
│  - TailwindCSS for styling                              │
│  - Recharts for bandwidth graphs                        │
│  - React Query for data fetching                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Backend (Python FastAPI)                 │
│  - FastAPI for REST endpoints                           │
│  - Async HTTP client for OPNsense API                   │
│  - WebSocket for real-time updates                      │
│  - Caching layer for performance                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    OPNsense API                          │
│  - REST API with key/secret authentication              │
│  - HTTPS connection to firewall                         │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
opnsense_power/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings & env vars
│   │   ├── opnsense_client.py   # OPNsense API wrapper
│   │   └── routers/
│   │       ├── dhcp.py          # DHCP endpoints
│   │       ├── vlans.py         # VLAN endpoints
│   │       ├── arp.py           # ARP/devices endpoints
│   │       ├── interfaces.py    # Interface stats
│   │       └── shapers.py       # Traffic shaper endpoints
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DHCPLeases.tsx
│   │   │   ├── VLANList.tsx
│   │   │   ├── ARPTable.tsx
│   │   │   ├── InterfaceStats.tsx
│   │   │   └── TrafficShapers.tsx
│   │   ├── hooks/
│   │   │   └── useOPNsense.ts   # API hooks
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml           # Easy deployment
├── .env.example
└── README.md
```

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Set up Python FastAPI backend structure
- [ ] Create OPNsense API client with authentication
- [ ] Set up React frontend with Vite + TailwindCSS
- [ ] Create basic layout/navigation

### Phase 2: Core Features
- [ ] Implement DHCP leases endpoint & UI
- [ ] Implement ARP table (devices) endpoint & UI
- [ ] Implement VLAN listing endpoint & UI
- [ ] Implement interface statistics endpoint & UI

### Phase 3: Traffic Shapers (Real-time)
- [ ] Implement traffic shaper configuration endpoint
- [ ] Add real-time bandwidth statistics
- [ ] Create visual bandwidth usage bars/charts
- [ ] Add WebSocket for live updates (polling as fallback)

### Phase 4: Polish
- [ ] Add search/filter functionality
- [ ] Add auto-refresh controls
- [ ] Error handling & loading states
- [ ] Docker deployment setup

---

## OPNsense API Authentication

The app will need:
1. **API Key** - Generated in OPNsense (System → Access → Users)
2. **API Secret** - One-time download when key is created
3. **Base URL** - e.g., `https://192.168.1.1`

These will be stored in environment variables:
```env
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your-api-key
OPNSENSE_API_SECRET=your-api-secret
OPNSENSE_VERIFY_SSL=false  # For self-signed certs
```

---

## UI Mockup Concept

```
┌──────────────────────────────────────────────────────────────┐
│  🔥 OPNsense Monitor                        [Auto-refresh ◉] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ DHCP Leases (24) ──────────────────────────────────────┐ │
│  │ IP            MAC                Hostname      Expires  │ │
│  │ 192.168.1.10  aa:bb:cc:dd:ee:ff  desktop-pc    2h 30m  │ │
│  │ 192.168.1.11  11:22:33:44:55:66  iphone-john   1h 15m  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Traffic Shapers ───────────────────────────────────────┐ │
│  │ VLAN10-Download (100 Mbps)                              │ │
│  │ ████████████████████░░░░░░░░░░  67.3 Mbps (67%)        │ │
│  │                                                         │ │
│  │ VLAN20-Upload (50 Mbps)                                 │ │
│  │ ████████░░░░░░░░░░░░░░░░░░░░░░  12.8 Mbps (26%)        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ VLANs ─────────────┐  ┌─ Network Devices (ARP) ───────┐ │
│  │ ID   Name      IPs  │  │ IP           MAC        Vendor │ │
│  │ 10   Servers   5    │  │ 192.168.1.1  aa:bb:...  Cisco  │ │
│  │ 20   IoT       12   │  │ 192.168.1.2  cc:dd:...  Apple  │ │
│  │ 30   Guests    3    │  │ ...                            │ │
│  └─────────────────────┘  └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Questions Before Implementation

1. **Single or Multiple OPNsense instances?**
   - Single firewall or multiple to monitor?

2. **Refresh rate for real-time data?**
   - Every 1s, 5s, 10s for traffic shapers?

3. **Historical data needed?**
   - Just live view, or store history for graphs?

4. **Authentication for the web app?**
   - Open access (local network) or login required?

5. **Deployment preference?**
   - Docker, bare metal, or specific hosting?

---

## Ready to Implement?

Once you confirm the plan and answer the questions above, I'll start building Phase 1!
