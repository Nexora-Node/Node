#!/usr/bin/env python3
"""
Nexora CLI - Distributed Node Network Client
Command-line interface for managing Nexora nodes with anti-cheat features
"""

import argparse
import sys
import os
import json
import time
import hashlib
import platform
import socket
import uuid
import secrets
import threading
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_DIR = Path.home() / ".nexora"
CONFIG_FILE = CONFIG_DIR / "config.json"
PID_FILE = CONFIG_DIR / "node.pid"
DEFAULT_API_URL = os.environ.get("NEXORA_API_URL", "https://node-production-712b.up.railway.app")

# ── SUPPORTED CHAINS (mirrors backend) ───────────────────────────────────────
CHAIN_INFO = {
    1:        {"name": "ETH Mainnet",   "multiplier": 5.0},
    10:       {"name": "OP Mainnet",    "multiplier": 2.0},
    56:       {"name": "BNB Chain",     "multiplier": 2.0},
    8453:     {"name": "Base Mainnet",  "multiplier": 3.0},
    84532:    {"name": "Base Sepolia",  "multiplier": 1.5},
    11155111: {"name": "ETH Sepolia",   "multiplier": 1.5},
    11155420: {"name": "OP Sepolia",    "multiplier": 1.5},
    97:       {"name": "BNB Testnet",   "multiplier": 1.2},
}

# Common local RPC ports to probe
LOCAL_RPC_PORTS = [8545, 8546, 9545, 9546, 7545]


class NexoraCLI:
    """Main CLI class for Nexora node management"""
    
    def __init__(self):
        self.config = self.load_config()
        self.api_url = self.config.get("api_url", DEFAULT_API_URL)
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self, config: dict):
        """Save configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def generate_device_id(self) -> str:
        """
        Generate unique device ID using:
        - OS
        - hostname
        - MAC address
        Hash with SHA256
        """
        os_info = f"{platform.system()}-{platform.release()}-{platform.machine()}"
        hostname = socket.gethostname()
        
        # Get MAC address
        mac = uuid.getnode()
        mac_address = ':'.join(f'{(mac >> i) & 0xff:02x}' for i in range(0, 48, 8))
        
        # Create hash from combined info
        combined = f"{os_info}:{hostname}:{mac_address}"
        device_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
        
        return device_id
    
    def generate_device_fingerprint(self) -> str:
        """
        Generate enhanced device fingerprint using:
        - OS
        - hostname
        - MAC address
        - CPU count
        - RAM size
        - disk size
        Hash with SHA256
        """
        os_info = f"{platform.system()}-{platform.release()}-{platform.machine()}"
        hostname = socket.gethostname()
        
        # Get MAC address
        mac = uuid.getnode()
        mac_address = ':'.join(f'{(mac >> i) & 0xff:02x}' for i in range(0, 48, 8))
        
        # Get CPU count
        cpu_count = os.cpu_count() or 1
        
        # Get RAM size (approximate)
        try:
            import psutil
            ram_size = psutil.virtual_memory().total // (1024**3)  # GB
        except:
            ram_size = 0
        
        # Get disk size (approximate)
        try:
            import psutil
            disk_size = psutil.disk_usage('/').total // (1024**3)  # GB
        except:
            disk_size = 0
        
        # Create hash from combined info
        combined = f"{os_info}:{hostname}:{mac_address}:{cpu_count}:{ram_size}:{disk_size}"
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()
        
        return fingerprint
    
    def generate_node_id(self) -> str:
        """Generate unique node ID"""
        device_id = self.config.get("device_id", "unknown")
        timestamp = str(int(time.time()))
        salt = secrets.token_hex(4)
        
        combined = f"{device_id}:{timestamp}:{salt}"
        node_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
        
        return node_id
    
    def detect_local_chain_nodes(self) -> list:
        """
        Probe common local RPC ports to find running blockchain nodes.
        Returns list of {port, chain_id, chain_name, rpc_url, block_number}
        """
        found = []
        for port in LOCAL_RPC_PORTS:
            rpc_url = f"http://127.0.0.1:{port}"
            try:
                # Get chain ID
                r = requests.post(rpc_url, json={
                    "jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1
                }, timeout=2)
                chain_id_hex = r.json().get("result")
                if not chain_id_hex:
                    continue
                chain_id = int(chain_id_hex, 16)

                # Get block number
                r2 = requests.post(rpc_url, json={
                    "jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1
                }, timeout=2)
                block_hex = r2.json().get("result")
                block = int(block_hex, 16) if block_hex else 0

                chain_name = CHAIN_INFO.get(chain_id, {}).get("name", f"Unknown ({chain_id})")
                multiplier = CHAIN_INFO.get(chain_id, {}).get("multiplier", 1.0)

                found.append({
                    "port": port,
                    "chain_id": chain_id,
                    "chain_name": chain_name,
                    "rpc_url": rpc_url,
                    "block_number": block,
                    "multiplier": multiplier,
                })
            except Exception:
                continue
        return found

    def generate_proof_of_work(self, device_id: str, difficulty: int = 3) -> str:
        """
        Generate proof-of-work nonce
        
        Args:
            device_id: Device ID
            difficulty: Number of leading zeros required
        
        Returns:
            Nonce value
        """
        nonce = 0
        target = "0" * difficulty
        
        while True:
            data = f"{device_id}{nonce}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()
            if hash_result.startswith(target):
                return str(nonce)
            nonce += 1
    
    def register(self, referral_code: str):
        """Register a new user with referral code"""
        print(f"\n{'='*50}")
        print("NEXORA REGISTRATION")
        print(f"{'='*50}\n")
        
        # Get username
        username = input("Enter username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            return
        
        # Generate device ID and fingerprint
        device_id = self.generate_device_id()
        device_fingerprint = self.generate_device_fingerprint()
        
        print(f"\nGenerated Device ID: {device_id}")
        print(f"Generated Fingerprint: {device_fingerprint[:16]}...")
        
        # Register user
        print("\nRegistering user...")
        try:
            response = requests.post(
                f"{self.api_url}/user/register",
                json={
                    "username": username,
                    "referral_code": referral_code
                },
                timeout=10
            )
            
            if response.status_code == 201:
                user_data = response.json()
                print(f"✓ User registered successfully!")
                print(f"  Username: {user_data['username']}")
                print(f"  Your Referral Code: {user_data['referral_code']}")
                
                # Register device
                print("\nRegistering device...")
                device_response = requests.post(
                    f"{self.api_url}/user/device/register",
                    json={
                        "device_id": device_id,
                        "device_fingerprint": device_fingerprint,
                        "user_id": user_data['id']
                    },
                    timeout=10
                )
                
                if device_response.status_code == 201:
                    print("✓ Device registered successfully!")

                    # Optional: link wallet address
                    print("\nWallet Address (optional, press Enter to skip):")
                    print("  Link your EVM wallet to receive future token rewards.")
                    wallet = input("  Wallet (0x...): ").strip()
                    if wallet:
                        try:
                            wr = requests.patch(
                                f"{self.api_url}/user/{username}/wallet",
                                json={"wallet_address": wallet},
                                timeout=10,
                            )
                            if wr.status_code == 200:
                                print(f"✓ Wallet linked: {wallet[:10]}...{wallet[-6:]}")
                            else:
                                print(f"  ✗ Wallet not linked: {wr.json().get('detail', 'invalid address')}")
                        except Exception:
                            print("  ✗ Could not link wallet (you can do this later)")

                    # Save config
                    config = {
                        "username": username,
                        "device_id": device_id,
                        "device_fingerprint": device_fingerprint,
                        "referral_code": user_data['referral_code'],
                        "api_url": self.api_url,
                        "registered_at": datetime.utcnow().isoformat()
                    }
                    self.save_config(config)
                    print("\n✓ Configuration saved!")
                    print(f"\nYou can now start your node with: python main.py start")
                else:
                    print(f"✗ Device registration failed: {device_response.text}")
            else:
                print(f"✗ Registration failed: {response.json().get('detail', 'Unknown error')}")
        
        except requests.exceptions.ConnectionError:
            print("✗ Error: Cannot connect to server. Make sure the backend is running.")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    def start_node(self, daemon: bool = False):
        """Start node - resume existing node or register new one"""
        print(f"\n{'='*50}")
        print("NEXORA NODE START")
        print(f"{'='*50}\n")

        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                alive = False
                if platform.system() == "Windows":
                    # Check via tasklist — more reliable than OpenProcess
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                        capture_output=True, text=True
                    )
                    alive = str(pid) in result.stdout
                else:
                    try:
                        os.kill(pid, 0)
                        alive = True
                    except OSError:
                        pass
                if alive:
                    print("✗ Node is already running!")
                    print(f"  Use 'python main.py stop' to stop it first.")
                    return
                else:
                    PID_FILE.unlink()  # stale PID
            except Exception:
                PID_FILE.unlink()

        # Re-launch as detached background process so terminal can be closed
        if not daemon:
            script = os.path.abspath(__file__)
            log_file = CONFIG_DIR / "node.log"
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if platform.system() == "Windows":
                with open(log_file, "w") as lf:
                    proc = subprocess.Popen(
                        [sys.executable, script, "start", "--daemon"],
                        stdout=lf, stderr=lf,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                        close_fds=True,
                    )
            else:
                with open(log_file, "w") as lf:
                    proc = subprocess.Popen(
                        [sys.executable, script, "start", "--daemon"],
                        stdout=lf, stderr=lf,
                        start_new_session=True,
                        close_fds=True,
                    )
            # Save daemon PID immediately so next 'start' detects it
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            PID_FILE.write_text(str(proc.pid))
            print(f"✓ Node started in background (PID: {proc.pid})")
            print(f"  Logs : {log_file}")
            print(f"  Use 'python main.py status' to check status")
            print(f"  Use 'python main.py stop' to stop the node")
            print(f"\n  You can safely close this terminal.")
            return

        if not self.config.get("device_id"):
            print("✗ Error: Not registered!")
            print("  Use 'python main.py register --ref CODE' to register first.")
            return

        device_id = self.config["device_id"]

        # Try to resume existing node first
        node_info_file = CONFIG_DIR / "node_info.json"
        node_id = None
        node_token = None

        if node_info_file.exists():
            try:
                with open(node_info_file, 'r') as f:
                    saved = json.load(f)
                node_id = saved.get("node_id")
                node_token = saved.get("node_token")

                # Verify node still valid on server before resuming
                try:
                    test = requests.post(
                        f"{self.api_url}/node/heartbeat",
                        json={"node_id": node_id, "node_token": node_token,
                              "device_id": device_id, "uptime": 0.0},
                        timeout=5,
                    )
                    if test.status_code == 401 or (test.status_code == 400 and "not found" in test.text.lower()):
                        print(f"Saved node no longer valid, registering new node...")
                        node_id = None
                        node_token = None
                        node_info_file.unlink(missing_ok=True)
                    else:
                        print(f"Device ID: {device_id}")
                        print(f"Resuming node: {node_id}")
                except Exception:
                    # Can't verify — try to resume anyway
                    print(f"Device ID: {device_id}")
                    print(f"Resuming node: {node_id}")
            except Exception:
                node_id = None

        # If no saved node, register a new one
        if not node_id or not node_token:
            print(f"Device ID: {device_id}")
            print("\nGenerating proof-of-work...")
            nonce = self.generate_proof_of_work(device_id)
            print(f"Nonce: {nonce}")
            print("\nRegistering new node...")
            try:
                response = requests.post(
                    f"{self.api_url}/node/register",
                    json={
                        "device_id": device_id,
                        "system": f"{platform.system()}-{platform.release()}",
                        "hostname": socket.gethostname(),
                        "nonce": nonce,
                    },
                    timeout=10,
                )
                if response.status_code == 200:
                    result = response.json()
                    node_id = result["node_id"]
                    node_token = result["node_token"]
                    print(f"✓ Node registered!")
                else:
                    print(f"✗ Failed to start node: {response.json().get('detail', 'Unknown error')}")
                    return
            except requests.exceptions.ConnectionError:
                print("✗ Cannot connect to server.")
                return
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                return

        # Save node info
        node_info = {
            "node_id": node_id,
            "node_token": node_token,
            "device_id": device_id,
            "started_at": datetime.utcnow().isoformat(),
        }
        with open(node_info_file, 'w') as f:
            json.dump(node_info, f, indent=2)

        self.config["node_token"] = node_token
        self.save_config(self.config)

        # Start heartbeat loop
        stop_event = threading.Event()
        thread = threading.Thread(
            target=self._node_loop,
            args=(node_id, node_token, device_id, stop_event),
            daemon=False,
        )
        thread.start()

        # Auto-detect and register local blockchain nodes
        print("\nScanning for local blockchain nodes...")
        chain_nodes = self.detect_local_chain_nodes()
        if chain_nodes:
            for cn in chain_nodes:
                print(f"  Found: {cn['chain_name']} on port {cn['port']} "
                      f"(block #{cn['block_number']:,}, {cn['multiplier']}x reward)")
            # Start chain heartbeat thread
            chain_thread = threading.Thread(
                target=self._chain_loop,
                args=(node_id, node_token, chain_nodes, stop_event),
                daemon=False,
            )
            chain_thread.start()

            # Save chain info
            chain_info_file = CONFIG_DIR / "chain_info.json"
            with open(chain_info_file, 'w') as f:
                json.dump(chain_nodes, f, indent=2)
        else:
            print("  No local blockchain nodes detected.")
            print("  Run a Base/ETH/OP node locally to earn bonus rewards!")

        pid = os.getpid()
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))

        print(f"✓ Node started (PID: {pid})")
        print(f"  Referral Code : {self.config.get('referral_code', 'N/A')} (share to invite others)")
        print(f"  Use 'python main.py status' to check status")
        print(f"  Use 'python main.py stop' to stop the node")

        try:
            while not stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping node...")
            stop_event.set()
            thread.join(timeout=5)
            if PID_FILE.exists():
                PID_FILE.unlink()
            print("✓ Node stopped")
    
    def _node_loop(self, node_id: str, node_token: str, device_id: str, stop_event: threading.Event):
        """Background node loop - sends heartbeats with jitter to avoid perfect-timing detection."""
        import random
        start_time = time.time()
        # Base interval 30 s ± up to 4 s of random jitter (always > 20 s server minimum)
        BASE_INTERVAL = 30
        JITTER = 4

        while not stop_event.is_set():
            try:
                uptime = time.time() - start_time
                response = requests.post(
                    f"{self.api_url}/node/heartbeat",
                    json={
                        "node_id": node_id,
                        "node_token": node_token,
                        "device_id": device_id,
                        "uptime": uptime,
                    },
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    earned = data.get('tokens_earned', 0)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat OK — +{earned:.6f} NEXORA (uptime: {uptime:.0f}s)")
                else:
                    error = response.json().get("detail", "Unknown error")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat failed: {error}")

            except requests.exceptions.ConnectionError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error - retrying...")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}")

            # Sleep with jitter — prevents perfect-timing detection on the server
            interval = BASE_INTERVAL + random.uniform(-JITTER, JITTER)
            for _ in range(int(interval)):
                if stop_event.is_set():
                    break
                time.sleep(1)
    
    def _chain_loop(self, node_id: str, node_token: str, chain_nodes: list, stop_event: threading.Event):
        """
        Background loop for chain node heartbeats.
        Registers each chain node then sends heartbeats every 60 seconds.
        """
        import random
        registered = {}  # chain_id → chain_node_id

        # Register all detected chain nodes
        for cn in chain_nodes:
            try:
                r = requests.post(
                    f"{self.api_url}/chain/register",
                    json={
                        "node_id": node_id,
                        "node_token": node_token,
                        "chain_id": cn["chain_id"],
                        "rpc_url": cn["rpc_url"],
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    data = r.json()
                    registered[cn["chain_id"]] = data["chain_node_id"]
                    print(f"[Chain] ✓ Registered {cn['chain_name']} "
                          f"({data['reward_multiplier']}x multiplier)")
                else:
                    print(f"[Chain] ✗ {cn['chain_name']}: {r.json().get('detail', 'error')}")
            except Exception as e:
                print(f"[Chain] ✗ {cn['chain_name']}: {str(e)}")

        if not registered:
            return

        # Heartbeat loop — every 60 seconds
        while not stop_event.is_set():
            for cn in chain_nodes:
                chain_id = cn["chain_id"]
                if chain_id not in registered:
                    continue
                try:
                    # Get current block
                    r = requests.post(cn["rpc_url"], json={
                        "jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1
                    }, timeout=3)
                    block_hex = r.json().get("result")
                    if not block_hex:
                        continue
                    local_block = int(block_hex, 16)

                    # Send chain heartbeat
                    hb = requests.post(
                        f"{self.api_url}/chain/heartbeat",
                        json={
                            "chain_node_id": registered[chain_id],
                            "node_id": node_id,
                            "node_token": node_token,
                            "local_block": local_block,
                        },
                        timeout=10,
                    )
                    if hb.status_code == 200:
                        data = hb.json()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"[Chain:{cn['chain_name']}] "
                              f"block={local_block:,} lag={data.get('sync_lag', '?')} "
                              f"+{data.get('bonus_tokens', data.get('bonus_points', 0)):.6f} NEXORA")
                    else:
                        print(f"[Chain:{cn['chain_name']}] {hb.json().get('detail', 'error')}")
                except Exception as e:
                    print(f"[Chain:{cn['chain_name']}] Error: {str(e)}")

            # Sleep 60s with jitter
            interval = 60 + random.uniform(-5, 5)
            for _ in range(int(interval)):
                if stop_event.is_set():
                    break
                time.sleep(1)

    def stop_node(self):
        """Stop running node and notify server"""
        print(f"\n{'='*50}")
        print("NEXORA NODE STOP")
        print(f"{'='*50}\n")

        if not PID_FILE.exists():
            print("✗ No node is running!")
            return

        # Notify server to set node status = stopped
        node_info_file = CONFIG_DIR / "node_info.json"
        if node_info_file.exists():
            try:
                with open(node_info_file, 'r') as f:
                    node_info = json.load(f)
                requests.post(
                    f"{self.api_url}/node/stop",
                    json={
                        "node_id": node_info["node_id"],
                        "node_token": node_info["node_token"],
                        "device_id": node_info["device_id"],
                    },
                    timeout=5,
                )
            except Exception:
                pass  # Best effort — still stop locally
        
        try:
            # Read PID
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to kill process
            if platform.system() == "Windows":
                os.system(f"taskkill /PID {pid} /F >nul 2>&1")
            else:
                os.kill(pid, 15)  # SIGTERM
            
            # Remove PID file
            PID_FILE.unlink()
            
            # Remove node info
            node_info_file = CONFIG_DIR / "node_info.json"
            if node_info_file.exists():
                node_info_file.unlink()
            
            print("✓ Node stopped successfully!")
        
        except ProcessLookupError:
            print("✗ Process not found. Removing stale PID file.")
            PID_FILE.unlink()
        except Exception as e:
            print(f"✗ Error stopping node: {str(e)}")
    
    def set_wallet(self, wallet_address: str):
        """Link or update wallet address"""
        print(f"\n{'='*50}")
        print("NEXORA WALLET LINK")
        print(f"{'='*50}\n")

        if not self.config.get("username"):
            print("✗ Not registered!")
            return

        try:
            r = requests.patch(
                f"{self.api_url}/user/{self.config['username']}/wallet",
                json={"wallet_address": wallet_address},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                print(f"✓ Wallet linked: {data['wallet_address']}")
                print(f"  Your tokens will be distributed to this address on token launch.")
            else:
                print(f"✗ {r.json().get('detail', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to server.")
        except Exception as e:
            print(f"✗ Error: {str(e)}")

    def claim(self):
        """Claim available NEXORA"""
        print(f"\n{'='*50}")
        print("NEXORA CLAIM")
        print(f"{'='*50}\n")
        print("To claim your NEXORA tokens, open the dashboard:")
        print("  https://node-delta-ten.vercel.app")
        print("\nClaim is done on-chain via the web dashboard.")
        print("Make sure your wallet is linked first.")

    def status(self):
        """Show node and reward status"""
        print(f"\n{'='*50}")
        print("NEXORA STATUS")
        print(f"{'='*50}\n")

        if not self.config.get("username"):
            print("✗ Not registered!")
            print("  Use 'python main.py register --ref CODE' to register.")
            return

        print(f"Username: {self.config['username']}")
        print(f"Device ID: {self.config['device_id']}")
        print(f"Referral Code: {self.config['referral_code']} (share to invite others)")

        # Check if node is running
        if PID_FILE.exists():
            print(f"\nNode Status: RUNNING")

            node_info_file = CONFIG_DIR / "node_info.json"
            if node_info_file.exists():
                with open(node_info_file, 'r') as f:
                    node_info = json.load(f)
                print(f"Node ID: {node_info['node_id']}")
                print(f"Started: {node_info['started_at']}")

            chain_info_file = CONFIG_DIR / "chain_info.json"
            if chain_info_file.exists():
                with open(chain_info_file, 'r') as f:
                    chains = json.load(f)
                if chains:
                    print(f"\nBlockchain Nodes:")
                    for cn in chains:
                        print(f"  {cn['chain_name']} — port {cn['port']} — {cn['multiplier']}x reward")
        else:
            print(f"\nNode Status: STOPPED")

        # Get NEXORA balance
        try:
            response = requests.get(
                f"{self.api_url}/tokens/{self.config['username']}",
                timeout=10
            )

            if response.status_code == 200:
                t = response.json()
                print(f"\nNEXORA Balance:")
                print(f"  Available : {t['tokens']:.6f} NEXORA")
                print(f"  Total Earned: {t['total_earned']:.6f} NEXORA")
                print(f"  Claimed   : {t['claimed_tokens']:.6f} NEXORA")
                user_r = requests.get(f"{self.api_url}/user/{self.config['username']}", timeout=10)
                if user_r.status_code == 200:
                    w = user_r.json().get("wallet_address")
                    if w:
                        print(f"  Wallet    : {w[:10]}...{w[-6:]}")
                    else:
                        print(f"  Wallet    : not linked (run: python main.py wallet 0xYOUR_ADDRESS)")
                print(f"\n  → Claim at: https://node-delta-ten.vercel.app")
            else:
                print(f"\nNEXORA: Unable to fetch")

        except requests.exceptions.ConnectionError:
            print(f"\nNEXORA: Unable to connect to server")
        except Exception as e:
            print(f"\nNEXORA: Error - {str(e)}")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        prog="nexora",
        description="Nexora CLI - Distributed Node Network Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py register --ref YOUR_REF_CODE
  python main.py start
  python main.py status
  python main.py stop
  python main.py claim
  python main.py wallet 0xYourWalletAddress
  python main.py chains

Dashboard: https://node-delta-ten.vercel.app
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register a new user")
    register_parser.add_argument(
        "--ref",
        required=True,
        help="Referral code (required)"
    )
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start node in background")
    start_parser.add_argument("--daemon", action="store_true", help=argparse.SUPPRESS)
    
    # Stop command
    subparsers.add_parser("stop", help="Stop running node")
    
    # Status command
    subparsers.add_parser("status", help="Show node and reward status")
    
    # Claim command
    subparsers.add_parser("claim", help="Claim available tokens")

    # Wallet command
    wallet_parser = subparsers.add_parser("wallet", help="Link EVM wallet address to your account")
    wallet_parser.add_argument("address", help="EVM wallet address (0x...)")

    # Chains command
    subparsers.add_parser("chains", help="List supported blockchain networks")

    # Parse arguments
    args = parser.parse_args()
    
    # Create CLI instance
    cli = NexoraCLI()
    
    # Execute command
    if args.command == "register":
        cli.register(args.ref)
    elif args.command == "start":
        cli.start_node(daemon=getattr(args, "daemon", False))
    elif args.command == "stop":
        cli.stop_node()
    elif args.command == "status":
        cli.status()
    elif args.command == "claim":
        cli.claim()
    elif args.command == "wallet":
        cli.set_wallet(args.address)
    elif args.command == "chains":
        try:
            r = requests.get(f"{cli.api_url}/chain/supported", timeout=10)
            print(f"\n{'='*50}")
            print("SUPPORTED BLOCKCHAIN NETWORKS")
            print(f"{'='*50}")
            for c in r.json():
                print(f"  {c['name']:<20} chain_id={c['chain_id']:<10} {c['multiplier']}x reward")
        except Exception as e:
            print(f"Error: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
