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
import requests
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_DIR = Path.home() / ".nexora"
CONFIG_FILE = CONFIG_DIR / "config.json"
PID_FILE = CONFIG_DIR / "node.pid"
DEFAULT_API_URL = os.environ.get("NEXORA_API_URL", "https://nexora-production.up.railway.app")


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
    
    def start_node(self):
        """Start node in background"""
        print(f"\n{'='*50}")
        print("NEXORA NODE START")
        print(f"{'='*50}\n")
        
        # Check if already running
        if PID_FILE.exists():
            print("✗ Node is already running!")
            print(f"  Use 'python main.py stop' to stop it first.")
            return
        
        # Check config
        if not self.config.get("device_id"):
            print("✗ Error: Not registered!")
            print("  Use 'python main.py register --ref CODE' to register first.")
            return
        
        device_id = self.config["device_id"]
        node_id = self.generate_node_id()
        
        print(f"Device ID: {device_id}")
        print(f"Node ID: {node_id}")
        
        # Generate proof-of-work
        print("\nGenerating proof-of-work...")
        nonce = self.generate_proof_of_work(device_id)
        print(f"Nonce: {nonce}")
        
        # Register node with server
        print("\nStarting node...")
        try:
            response = requests.post(
                f"{self.api_url}/node/register",
                json={
                    "device_id": device_id,
                    "system": f"{platform.system()}-{platform.release()}",
                    "hostname": socket.gethostname(),
                    "nonce": nonce
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                node_id = result["node_id"]
                node_token = result["node_token"]
                
                print("✓ Node registered with server!")
                print(f"Node Token: {node_token[:16]}...")
                
                # Save node token
                self.config["node_token"] = node_token
                self.save_config(self.config)
                
                # Start background thread
                stop_event = threading.Event()
                thread = threading.Thread(
                    target=self._node_loop,
                    args=(node_id, node_token, device_id, stop_event),
                    daemon=False
                )
                thread.start()
                
                # Save PID
                pid = os.getpid()
                with open(PID_FILE, 'w') as f:
                    f.write(str(pid))
                
                # Save node info
                node_info = {
                    "node_id": node_id,
                    "node_token": node_token,
                    "device_id": device_id,
                    "started_at": datetime.utcnow().isoformat()
                }
                node_info_file = CONFIG_DIR / "node_info.json"
                with open(node_info_file, 'w') as f:
                    json.dump(node_info, f, indent=2)
                
                print(f"✓ Node started in background (PID: {pid})")
                print(f"  Heartbeat interval: 30 seconds")
                print(f"  Use 'python main.py status' to check status")
                print(f"  Use 'python main.py stop' to stop the node")
                
                # Keep main thread alive
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
            
            else:
                print(f"✗ Failed to start node: {response.json().get('detail', 'Unknown error')}")
        
        except requests.exceptions.ConnectionError:
            print("✗ Error: Cannot connect to server. Make sure the backend is running.")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
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
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat sent (uptime: {uptime:.0f}s)")
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
    
    def stop_node(self):
        """Stop running node"""
        print(f"\n{'='*50}")
        print("NEXORA NODE STOP")
        print(f"{'='*50}\n")
        
        if not PID_FILE.exists():
            print("✗ No node is running!")
            return
        
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
    
    def claim(self):
        """Claim available points"""
        print(f"\n{'='*50}")
        print("NEXORA CLAIM POINTS")
        print(f"{'='*50}\n")

        if not self.config.get("username"):
            print("✗ Not registered! Use 'python main.py register --ref CODE' first.")
            return

        username = self.config["username"]
        try:
            response = requests.post(
                f"{self.api_url}/points/claim",
                json={"username": username},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {data['message']}")
            else:
                print(f"✗ {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to server.")
        except Exception as e:
            print(f"✗ Error: {str(e)}")

    def status(self):
        """Show node and reward status"""
        print(f"\n{'='*50}")
        print("NEXORA STATUS")
        print(f"{'='*50}\n")
        
        # Check if registered
        if not self.config.get("username"):
            print("✗ Not registered!")
            print("  Use 'python main.py register --ref CODE' to register.")
            return
        
        print(f"Username: {self.config['username']}")
        print(f"Device ID: {self.config['device_id']}")
        print(f"Referral Code: {self.config['referral_code']}")
        
        # Check if node is running
        if PID_FILE.exists():
            print(f"\nNode Status: RUNNING")
            
            # Load node info
            node_info_file = CONFIG_DIR / "node_info.json"
            if node_info_file.exists():
                with open(node_info_file, 'r') as f:
                    node_info = json.load(f)
                print(f"Node ID: {node_info['node_id']}")
                print(f"Started: {node_info['started_at']}")
        else:
            print(f"\nNode Status: STOPPED")
        
        # Get points info
        try:
            response = requests.get(
                f"{self.api_url}/points/{self.config['username']}",
                timeout=10
            )
            
            if response.status_code == 200:
                points = response.json()
                print(f"\nPoints:")
                print(f"  Available: {points['points']:.2f}")
                print(f"  Total Earned: {points['total_earned']:.2f}")
            else:
                print(f"\nPoints: Unable to fetch")
        
        except requests.exceptions.ConnectionError:
            print(f"\nPoints: Unable to connect to server")
        except Exception as e:
            print(f"\nPoints: Error - {str(e)}")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        prog="nexora",
        description="Nexora CLI - Distributed Node Network Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py register --ref NEXORA001
  python main.py start
  python main.py status
  python main.py stop
  python main.py claim
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
    subparsers.add_parser("start", help="Start node in background")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop running node")
    
    # Status command
    subparsers.add_parser("status", help="Show node and reward status")
    
    # Claim command
    subparsers.add_parser("claim", help="Claim available points")

    # Parse arguments
    args = parser.parse_args()
    
    # Create CLI instance
    cli = NexoraCLI()
    
    # Execute command
    if args.command == "register":
        cli.register(args.ref)
    elif args.command == "start":
        cli.start_node()
    elif args.command == "stop":
        cli.stop_node()
    elif args.command == "status":
        cli.status()
    elif args.command == "claim":
        cli.claim()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
