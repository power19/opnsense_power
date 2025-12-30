# OPNsense Monitor

A simple, real-time web dashboard to monitor your OPNsense firewall.

## Features

- **DHCP Leases** - View all active DHCP leases with IP, MAC, hostname, and expiry
- **Network Devices (ARP)** - Discover all devices on your network with vendor lookup
- **VLANs** - List all configured VLANs
- **Interface Statistics** - Real-time traffic stats for all interfaces
- **Traffic Shapers** - Live bandwidth usage with visual progress bars

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Vite + React + TypeScript                            │
│  - TailwindCSS for styling                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Backend (Python FastAPI)                 │
│  - FastAPI REST endpoints                               │
│  - Async HTTP client for OPNsense API                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    OPNsense API                          │
│  - REST API with key/secret authentication              │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- OPNsense firewall with API access enabled

## Setup

### 1. Create OPNsense API Key

1. Log into OPNsense web interface
2. Go to **System → Access → Users**
3. Edit your user (or create a new one)
4. Scroll to **API keys** section
5. Click **+** to create a new key
6. Download the key file (contains key and secret)

### 2. Configure Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` with your OPNsense details:

```env
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your-api-key-here
OPNSENSE_API_SECRET=your-api-secret-here
OPNSENSE_VERIFY_SSL=false
```

### 3. Configure Frontend

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /dhcp/leases` | DHCP lease list |
| `GET /arp/table` | ARP table (network devices) |
| `GET /vlans/list` | VLAN configuration |
| `GET /interfaces/statistics` | Interface traffic stats |
| `GET /shapers/config` | Traffic shaper configuration |
| `GET /shapers/statistics` | Live bandwidth usage |

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPNSENSE_URL` | OPNsense URL | `https://192.168.1.1` |
| `OPNSENSE_API_KEY` | API key | Required |
| `OPNSENSE_API_SECRET` | API secret | Required |
| `OPNSENSE_VERIFY_SSL` | Verify SSL cert | `false` |

## Project Structure

```
opnsense_power/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── opnsense_client.py   # OPNsense API wrapper
│   │   └── routers/             # API endpoints
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   └── App.tsx              # Main app
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## License

MIT
