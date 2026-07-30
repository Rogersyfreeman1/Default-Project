import subprocess
import sys
import os
import json
import datetime
import re
import signal
from pathlib import Path

RULES_FILE = Path(__file__).parent / "firewall_rules.json"
LOG_FILE = Path(__file__).parent / "firewall_log.txt"


def load_rules():
    if RULES_FILE.exists():
        return json.loads(RULES_FILE.read_text())
    return {"blocked_ips": [], "blocked_ports": [], "allowed_ips": [], "rules": []}


def save_rules(rules):
    RULES_FILE.write_text(json.dumps(rules, indent=2))


def log_action(action, detail):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action}: {detail}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line.strip())


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr, result.returncode


def block_ip(ip, name=None):
    if not name:
        name = f"Block_{ip.replace('.', '_')}"
    cmd = f'netsh advfirewall firewall add rule name="{name}" dir=in action=block remoteip={ip}'
    out, err, code = run_cmd(cmd)
    if code == 0:
        rules = load_rules()
        if ip not in rules["blocked_ips"]:
            rules["blocked_ips"].append(ip)
            save_rules(rules)
        log_action("BLOCK_IP", f"Blocked {ip} ({name})")
        return True
    log_action("BLOCK_IP_FAILED", f"{ip}: {err}")
    return False


def unblock_ip(ip):
    rules = load_rules()
    name = f"Block_{ip.replace('.', '_')}"
    cmd = f'netsh advfirewall firewall delete rule name="{name}"'
    out, err, code = run_cmd(cmd)
    if ip in rules["blocked_ips"]:
        rules["blocked_ips"].remove(ip)
        save_rules(rules)
    log_action("UNBLOCK_IP", f"Unblocked {ip}")
    return code == 0


def block_port(port, protocol="TCP", name=None):
    if not name:
        name = f"BlockPort_{port}_{protocol}"
    cmd = f'netsh advfirewall firewall add rule name="{name}" dir=in action=block protocol={protocol} localport={port}'
    out, err, code = run_cmd(cmd)
    if code == 0:
        rules = load_rules()
        entry = {"port": port, "protocol": protocol}
        if entry not in rules["blocked_ports"]:
            rules["blocked_ports"].append(entry)
            save_rules(rules)
        log_action("BLOCK_PORT", f"Blocked {protocol}/{port}")
        return True
    log_action("BLOCK_PORT_FAILED", f"{protocol}/{port}: {err}")
    return False


def unblock_port(port, protocol="TCP"):
    name = f"BlockPort_{port}_{protocol}"
    cmd = f'netsh advfirewall firewall delete rule name="{name}"'
    out, err, code = run_cmd(cmd)
    rules = load_rules()
    entry = {"port": port, "protocol": protocol}
    if entry in rules["blocked_ports"]:
        rules["blocked_ports"].remove(entry)
        save_rules(rules)
    log_action("UNBLOCK_PORT", f"Unblocked {protocol}/{port}")
    return code == 0


def block_outbound_ip(ip, name=None):
    if not name:
        name = f"BlockOut_{ip.replace('.', '_')}"
    cmd = f'netsh advfirewall firewall add rule name="{name}" dir=out action=block remoteip={ip}'
    out, err, code = run_cmd(cmd)
    if code == 0:
        log_action("BLOCK_OUTBOUND", f"Blocked outbound {ip}")
        return True
    log_action("BLOCK_OUTBOUND_FAILED", f"{ip}: {err}")
    return False


def show_connections():
    cmd = "netstat -ano"
    out, err, code = run_cmd(cmd)
    if code == 0:
        lines = out.strip().split("\n")
        header = lines[0] if lines else ""
        print(f"\n{'='*80}")
        print("ACTIVE NETWORK CONNECTIONS")
        print(f"{'='*80}")
        print(header)
        print(f"{'-'*80}")
        for line in lines[1:]:
            print(line)
        print(f"{'='*80}")
        print(f"Total: {len(lines)-1} connections\n")
    return out


def show_firewall_rules():
    cmd = 'netsh advfirewall firewall show rule name=all dir=in'
    out, err, code = run_cmd(cmd)
    if code == 0:
        print(f"\n{'='*80}")
        print("INBOUND FIREWALL RULES")
        print(f"{'='*80}")
        print(out)
    return out


def show_status():
    cmd = "netsh advfirewall show allprofiles state"
    out, err, code = run_cmd(cmd)
    print(f"\n{'='*80}")
    print("FIREWALL STATUS")
    print(f"{'='*80}")
    print(out)
    
    rules = load_rules()
    print(f"\nTracked blocked IPs: {rules['blocked_ips']}")
    print(f"Tracked blocked ports: {rules['blocked_ports']}")
    
    log_file = Path(__file__).parent / "firewall_log.txt"
    if log_file.exists():
        lines = log_file.read_text().strip().split("\n")
        print(f"\nLog entries: {len(lines)}")
    print(f"{'='*80}\n")
    return out


def monitor_connections(interval=5, filter_ip=None):
    print(f"\nMonitoring connections (refresh every {interval}s). Press Ctrl+C to stop.\n")
    seen = set()
    try:
        while True:
            cmd = "netstat -ano | findstr ESTABLISHED"
            out, err, code = run_cmd(cmd)
            rules = load_rules()
            blocked = set(rules["blocked_ips"])
            
            if out:
                for line in out.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 5:
                        remote = parts[2]
                        remote_ip = remote.split(":")[0] if ":" in remote else remote
                        
                        if filter_ip and filter_ip not in remote_ip:
                            continue
                        
                        key = line.strip()
                        if key not in seen:
                            seen.add(key)
                            status = " [BLOCKED]" if remote_ip in blocked else ""
                            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] {line.strip()}{status}")
            
            subprocess.run("timeout /t {} /nobreak >nul".format(interval), shell=True)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def scan_ports(target="127.0.0.1", ports=None):
    if not ports:
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080]
    
    print(f"\nScanning {target}...")
    print(f"{'='*60}")
    
    rules = load_rules()
    blocked = set(rules["blocked_ips"])
    
    for port in ports:
        cmd = f'powershell -Command "Test-NetConnection -ComputerName {target} -Port {port} -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"'
        out, err, code = run_cmd(cmd)
        is_open = "True" in out
        status = "OPEN" if is_open else "closed"
        icon = "[!]" if is_open else "[.]"
        print(f"  {icon} Port {port}: {status}")
    
    print(f"{'='*60}\n")


def enable_firewall():
    for profile in ["Domain", "Private", "Public"]:
        cmd = f'netsh advfirewall set {profile}profile state on'
        run_cmd(cmd)
    log_action("ENABLE", "Firewall enabled on all profiles")
    print("Firewall enabled on all profiles.")


def disable_firewall():
    for profile in ["Domain", "Private", "Public"]:
        cmd = f'netsh advfirewall set {profile}profile state off'
        run_cmd(cmd)
    log_action("DISABLE", "Firewall disabled on all profiles")
    print("WARNING: Firewall disabled on all profiles.")


def show_help():
    print(f"""
{'='*60}
  WINDOWS FIREWALL TOOL
{'='*60}

  STATUS & INFO
    status          Show firewall status and tracked rules
    connections     Show active network connections
    rules           Show all inbound firewall rules
    scan [ip]       Scan common ports on target (default: localhost)

  BLOCK
    block-ip <ip>           Block an IP address (inbound)
    block-port <port> [TCP|UDP]   Block a port
    block-out <ip>          Block outbound traffic to IP

  UNBLOCK
    unblock-ip <ip>         Unblock an IP address
    unblock-port <port> [TCP|UDP]  Unblock a port

  FIREWALL CONTROL
    enable          Enable firewall on all profiles
    disable         Disable firewall on all profiles (DANGEROUS)

  MONITOR
    monitor [sec]   Monitor live connections (default 5s refresh)
    monitor [sec] <ip>  Filter monitoring to specific IP

  OTHER
    log             Show recent log entries
    clear-log       Clear the log file
    help            Show this help
    exit            Exit

{'='*60}
""")


def show_log(n=20):
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text().strip().split("\n")
        print(f"\nLast {min(n, len(lines))} log entries:")
        print(f"{'-'*60}")
        for line in lines[-n:]:
            print(line)
        print(f"{'-'*60}\n")
    else:
        print("No log entries yet.")


def clear_log():
    if LOG_FILE.exists():
        LOG_FILE.write_text("")
    print("Log cleared.")


def main():
    os.system("title Windows Firewall Tool")
    
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        process_command(cmd)
        return
    
    print(f"\n{'='*60}")
    print("  WINDOWS FIREWALL TOOL")
    print("  Type 'help' for commands")
    print(f"{'='*60}\n")
    
    while True:
        try:
            user_input = input("firewall> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye.")
                break
            process_command(user_input)
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except Exception as e:
            print(f"Error: {e}")


def process_command(cmd):
    parts = cmd.split()
    if not parts:
        return
    
    action = parts[0].lower()
    
    if action == "help":
        show_help()
    elif action == "status":
        show_status()
    elif action == "connections" or action == "netstat":
        show_connections()
    elif action == "rules":
        show_firewall_rules()
    elif action == "block-ip" or action == "blockip":
        if len(parts) < 2:
            print("Usage: block-ip <ip> [name]")
        else:
            name = parts[2] if len(parts) > 2 else None
            block_ip(parts[1], name)
    elif action == "unblock-ip" or action == "unblockip":
        if len(parts) < 2:
            print("Usage: unblock-ip <ip>")
        else:
            unblock_ip(parts[1])
    elif action == "block-port" or action == "blockport":
        if len(parts) < 2:
            print("Usage: block-port <port> [TCP|UDP]")
        else:
            proto = parts[2].upper() if len(parts) > 2 else "TCP"
            block_port(int(parts[1]), proto)
    elif action == "unblock-port" or action == "unblockport":
        if len(parts) < 2:
            print("Usage: unblock-port <port> [TCP|UDP]")
        else:
            proto = parts[2].upper() if len(parts) > 2 else "TCP"
            unblock_port(int(parts[1]), proto)
    elif action == "block-out" or action == "blockout":
        if len(parts) < 2:
            print("Usage: block-out <ip>")
        else:
            block_outbound_ip(parts[1])
    elif action == "monitor":
        interval = int(parts[1]) if len(parts) > 1 else 5
        filter_ip = parts[2] if len(parts) > 2 else None
        monitor_connections(interval, filter_ip)
    elif action == "scan":
        target = parts[1] if len(parts) > 1 else "127.0.0.1"
        scan_ports(target)
    elif action == "enable":
        enable_firewall()
    elif action == "disable":
        confirm = input("Are you sure? This weakens your security (yes/no): ")
        if confirm.lower() == "yes":
            disable_firewall()
        else:
            print("Cancelled.")
    elif action == "log":
        n = int(parts[1]) if len(parts) > 1 else 20
        show_log(n)
    elif action == "clear-log":
        clear_log()
    else:
        print(f"Unknown command: {action}. Type 'help' for commands.")


if __name__ == "__main__":
    main()
