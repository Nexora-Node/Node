# Nexora - Distributed Node Network

A lightweight, cross-platform CLI-based distributed node network system.

## Features

- **Lightweight**: No heavy computation, only heartbeat tracking
- **Cross-platform**: Works on Linux, VPS, Windows Terminal, Android (Termux)
- **CLI-based**: Everything runs via command line
- **Referral System**: Users register with referral codes
- **Reward System**: Earn points based on node uptime
- **Anti-cheat**: Max 2 nodes per device, uptime validation

## Architecture

```
nexora/
├── backend/                    # FastAPI backend server
│   ├── main.py                # FastAPI application
│   ├── database.py            # SQLAlchemy database setup
│   ├── models.py              # User, Device, Node models
│   ├── schemas.py             # Pydantic schemas
│   ├── routes/                # API routes
│   │   ├── user_routes.py     # User endpoints
│   │   ├── node_routes.py     # Node endpoints
│   │   └── points_routes.py   # Points endpoints
│   └── services/              # Business logic
│       ├── user_service.py    # User operations
│       ├── node_service.py    # Node operations
│       └── points_service.py  # Points operations
├── cli/
│   └── main.py                # CLI application
├── requirements.txt           # Python dependencies
└── seed_database.py           # Create seed user
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Seed Database (First Time Only)

```bash
python seed_database.py
```

This creates a seed user with referral code `NEXORA001`.

### 3. Start Backend Server

```bash
cd backend
python main.py
```

The server will start on `http://localhost:8000`

### 4. Use CLI Commands

```bash
# Register with a referral code
python cli/main.py register --ref NEXORA001

# Start node in background
python cli/main.py start

# Check status
python cli/main.py status

# Stop node
python cli/main.py stop
```

## CLI Commands

### `python cli/main.py register --ref CODE`

Register a new user with a referral code.

**Example:**
```bash
python cli/main.py register --ref NEXORA001
```

**What it does:**
- Prompts for username
- Generates unique device ID (OS + hostname + MAC address)
- Registers user with backend
- Registers device with backend
- Saves configuration to `~/.nexora/config.json`

### `python cli/main.py start`

Start node in background mode.

**Example:**
```bash
python cli/main.py start
```

**What it does:**
- Registers node with backend
- Starts background thread
- Sends heartbeat every 30 seconds
- Tracks uptime
- Saves PID to `~/.nexora/node.pid`

### `python cli/main.py stop`

Stop running node.

**Example:**
```bash
python cli/main.py stop
```

**What it does:**
- Reads PID from `~/.nexora/node.pid`
- Kills the process
- Cleans up PID file

### `python cli/main.py status`

Show node and reward status.

**Example:**
```bash
python cli/main.py status
```

**Output:**
- Username and device ID
- Referral code
- Node status (RUNNING/STOPPED)
- Points information

## API Endpoints

### POST /user/register

Register a new user.

**Request:**
```json
{
  "username": "john",
  "referral_code": "NEXORA001"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john",
  "referral_code": "XYZ67890",
  "invited_by": "NEXORA001",
  "points": 0.0,
  "total_earned": 0.0,
  "created_at": "2024-01-01T00:00:00"
}
```

### POST /node/register

Register a new node.

**Request:**
```json
{
  "device_id": "abc123def456",
  "system": "Linux-5.15.0-x86_64",
  "hostname": "myserver"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Node registered successfully",
  "node_id": "node789xyz"
}
```

### POST /node/heartbeat

Send heartbeat from node.

**Request:**
```json
{
  "node_id": "node789xyz",
  "device_id": "abc123def456",
  "uptime": 3600.5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Heartbeat received"
}
```

### GET /node/status/{device_id}

Get status of all nodes on a device.

**Response:**
```json
[
  {
    "node_id": "node789xyz",
    "device_id": "abc123def456",
    "uptime": 3600.5,
    "last_seen": "2024-01-01T01:00:00",
    "status": "active"
  }
]
```

### GET /points/{username}

Get points information.

**Response:**
```json
{
  "username": "john",
  "points": 50.5,
  "total_earned": 150.5
}
```

### POST /points/claim

Claim available points.

**Request:**
```json
{
  "username": "john"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully claimed 50.50 points",
  "points_claimed": 50.5
}
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String(50) | Unique username |
| referral_code | String(20) | Unique referral code |
| invited_by | String(20) | Referral code of inviter |
| points | Float | Current claimable points |
| total_earned | Float | Total points earned |
| created_at | DateTime | Registration timestamp |

### Devices Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| device_id | String(64) | Unique device ID |
| user_id | Integer | Foreign key to users |
| created_at | DateTime | Registration timestamp |

### Nodes Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| node_id | String(64) | Unique node ID |
| device_id | String(64) | Foreign key to devices |
| uptime | Float | Total uptime in seconds |
| last_seen | DateTime | Last heartbeat timestamp |
| status | String(20) | Node status (active/stopped) |
| created_at | DateTime | Start timestamp |

## Rules

1. **Referral Required**: Users must provide a valid referral code to register
2. **Max 2 Nodes**: Each device can run maximum 2 nodes
3. **Uptime Tracking**: Node uptime is tracked via heartbeats
4. **Reward Formula**: 1 point per minute of uptime (uptime_seconds / 60)
5. **Lightweight**: No mining or heavy computation
6. **Anti-cheat**: 
   - Max 2 nodes per device
   - Validate uptime (no jumps)
   - Reject heartbeat spam (min 20 seconds between heartbeats)

## Configuration

Configuration is stored in `~/.nexora/config.json`:

```json
{
  "username": "john",
  "device_id": "abc123def456",
  "referral_code": "XYZ67890",
  "api_url": "http://localhost:8000",
  "registered_at": "2024-01-01T00:00:00"
}
```

## Cross-Platform Support

### Linux
```bash
python3 cli/main.py register --ref CODE
```

### Windows Terminal
```bash
python cli/main.py register --ref CODE
```

### Android (Termux)
```bash
pkg install python
pip install -r requirements.txt
python seed_database.py
cd backend
python main.py &
cd ..
python cli/main.py register --ref NEXORA001
python cli/main.py start
```

### VPS
```bash
# Install Python 3.8+
sudo apt update
sudo apt install python3 python3-pip

# Setup
pip3 install -r requirements.txt
python3 seed_database.py

# Start backend (use screen or tmux for persistence)
screen -S nexora-backend
python3 backend/main.py

# In another screen
screen -S nexora-cli
python3 cli/main.py register --ref NEXORA001
python3 cli/main.py start
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### "Cannot connect to server"

Make sure the backend is running:
```bash
cd backend
python main.py
```

### "Node is already running"

Stop the existing node:
```bash
python cli/main.py stop
```

### "Invalid referral code"

Use the seed referral code: `NEXORA001`

### "Maximum 2 nodes per device allowed"

Each device can only run 2 nodes. Stop an existing node before starting a new one.

### "Heartbeat spam detected"

Heartbeats must be at least 20 seconds apart. The CLI sends heartbeats every 30 seconds by default.

## License

MIT License
