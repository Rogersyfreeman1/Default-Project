import hashlib
import json
import os
import subprocess
import datetime
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "identity_config.json"
ALERTS_FILE = Path(__file__).parent / "identity_alerts.json"
REPORT_FILE = Path(__file__).parent / "identity_report.txt"
WATCH_FOLDERS = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads",
]
SENSITIVE_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".txt", ".csv", ".key", ".pem", ".pfx"]
ID_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "Credit Card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "Phone": r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",
    "IP Address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
}


def safe_read(filepath):
    try:
        return filepath.read_text(encoding="utf-8")
    except (PermissionError, OSError):
        return None


def safe_write(filepath, content):
    try:
        filepath.write_text(content, encoding="utf-8")
        return True
    except (PermissionError, OSError):
        return False


def load_config():
    data = safe_read(CONFIG_FILE)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    config = {
        "watch_folders": [str(f) for f in WATCH_FOLDERS],
        "email": "",
        "check_passwords": True,
        "monitor_files": True,
        "alert_on_usb": True,
        "last_scan": None,
    }
    save_config(config)
    return config


def save_config(config):
    safe_write(CONFIG_FILE, json.dumps(config, indent=2))


def load_alerts():
    data = safe_read(ALERTS_FILE)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []
    return []


def save_alerts(alerts):
    safe_write(ALERTS_FILE, json.dumps(alerts, indent=2))


def add_alert(severity, message):
    alerts = load_alerts()
    alerts.append({
        "time": datetime.datetime.now().isoformat(),
        "severity": severity,
        "message": message,
    })
    save_alerts(alerts)
    icon = {"HIGH": "[!!!]", "MEDIUM": "[!]", "LOW": "[i]"}.get(severity, "[?]")
    print(f"  {icon} {message}")


def check_password_leak(password):
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    import urllib.request
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            text = response.read().decode("utf-8")
            for line in text.splitlines():
                hash_suffix, count = line.split(":")
                if hash_suffix.strip() == suffix:
                    return int(count.strip())
    except Exception as e:
        return -1
    return 0


def password_checker():
    print(f"\n{'='*60}")
    print("  PASSWORD LEAK CHECKER")
    print(f"{'='*60}")
    print("  Checks if your password appears in known data breaches.")
    print("  Your password is NEVER sent in full - only a partial hash.")
    print(f"{'-'*60}\n")
    
    passwords = []
    print("  Enter passwords to check (empty line to finish):")
    while True:
        try:
            pw = input("  Password: ").strip()
            if not pw:
                break
            passwords.append(pw)
        except (EOFError, KeyboardInterrupt):
            break
    
    if not passwords:
        print("  No passwords entered.")
        return
    
    print(f"\n  Checking {len(passwords)} password(s)...\n")
    
    for i, pw in enumerate(passwords, 1):
        count = check_password_leak(pw)
        if count == -1:
            print(f"  {i}. Could not check (network error)")
        elif count > 0:
            print(f"  {i}. LEAKED {count:,} times! Change this password NOW!")
            add_alert("HIGH", f"Password found leaked {count:,} times in data breaches")
        else:
            print(f"  {i}. Not found in known leaks - looks safe")
    
    print(f"\n{'='*60}\n")


def scan_sensitive_files():
    print(f"\n{'='*60}")
    print("  SENSITIVE FILE SCANNER")
    print(f"{'='*60}")
    print("  Scanning for files that may contain personal information...\n")
    
    config = load_config()
    folders = [Path(f) for f in config["watch_folders"]]
    found = []
    
    for folder in folders:
        if not folder.exists():
            continue
        print(f"  Scanning: {folder}")
        for root, dirs, files in os.walk(folder):
            for fname in files:
                fpath = Path(root) / fname
                ext = fpath.suffix.lower()
                if ext in SENSITIVE_EXTENSIONS:
                    size = fpath.stat().st_size if fpath.exists() else 0
                    if ext in [".key", ".pem", ".pfx", ".p12"]:
                        add_alert("HIGH", f"Credential file found: {fpath.name}")
                        found.append(("HIGH", str(fpath), "Credential file"))
                    elif ext == ".csv":
                        add_alert("MEDIUM", f"Data file found: {fpath.name}")
                        found.append(("MEDIUM", str(fpath), "Data file"))
    
    if found:
        print(f"\n  Found {len(found)} sensitive file(s):")
        for severity, path, ftype in found:
            icon = {"HIGH": "[!!!]", "MEDIUM": "[!]", "LOW": "[i]"}[severity]
            print(f"    {icon} [{ftype}] {path}")
    else:
        print("\n  No sensitive files found in watched folders.")
    
    print(f"\n{'='*60}\n")
    return found


def scan_files_for_ids():
    print(f"\n{'='*60}")
    print("  PERSONAL DATA SCANNER")
    print(f"{'='*60}")
    print("  Scanning text files for SSN, credit cards, emails, phones...\n")
    
    config = load_config()
    folders = [Path(f) for f in config["watch_folders"]]
    findings = []
    
    for folder in folders:
        if not folder.exists():
            continue
        for root, dirs, files in os.walk(folder):
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() in [".txt", ".csv", ".log", ".doc", ".docx"]:
                    try:
                        content = fpath.read_text(errors="ignore")[:50000]
                        for id_type, pattern in ID_PATTERNS.items():
                            matches = re.findall(pattern, content)
                            if matches:
                                findings.append({
                                    "file": str(fpath),
                                    "type": id_type,
                                    "count": len(matches),
                                })
                                severity = "HIGH" if id_type in ["SSN", "Credit Card"] else "MEDIUM"
                                add_alert(severity, f"{len(matches)} {id_type}(s) found in {fpath.name}")
                    except:
                        pass
    
    if findings:
        print(f"\n  Found personal data in {len(findings)} location(s):")
        for f in findings:
            print(f"    {f['type']}: {f['count']} in {f['file']}")
    else:
        print("\n  No personal data patterns found.")
    
    print(f"\n{'='*60}\n")
    return findings


def check_network_security():
    print(f"\n{'='*60}")
    print("  NETWORK SECURITY CHECK")
    print(f"{'='*60}\n")
    
    suspicious_ports = [3389, 22, 23, 445, 135, 139, 1433, 3306, 5432]
    
    result = subprocess.run("netstat -ano", capture_output=True, text=True, shell=True)
    lines = result.stdout.strip().split("\n")
    
    listening = []
    external = []
    
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 5:
            proto = parts[0]
            local = parts[1]
            foreign = parts[2]
            state = parts[3]
            
            if state == "LISTENING":
                port = local.split(":")[-1] if ":" in local else ""
                if port.isdigit():
                    port = int(port)
                    if port in suspicious_ports:
                        add_alert("HIGH", f"Suspicious port {port} is listening ({proto})")
                        listening.append((port, proto))
            
            if state == "ESTABLISHED" and foreign != "0.0.0.0:0":
                foreign_ip = foreign.split(":")[0] if ":" in foreign else foreign
                if not foreign_ip.startswith("127.") and not foreign_ip.startswith("192.168."):
                    external.append((foreign_ip, foreign.split(":")[-1] if ":" in foreign else ""))
    
    if listening:
        print("  Suspicious open ports:")
        for port, proto in listening:
            print(f"    [!!!] Port {port} ({proto}) - commonly exploited")
    else:
        print("  No suspicious ports open.")
    
    if external:
        print(f"\n  External connections: {len(external)}")
        for ip, port in external[:10]:
            print(f"    -> {ip}:{port}")
    
    print(f"\n{'='*60}\n")


def check_usb_devices():
    print(f"\n{'='*60}")
    print("  USB DEVICE CHECK")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        "wmic diskdrive get model,size,mediatype,status",
        capture_output=True, text=True, shell=True
    )
    
    if result.stdout.strip():
        print(result.stdout)
    else:
        print("  Could not retrieve USB info.")
    
    print(f"\n{'='*60}\n")


def check_startup_programs():
    print(f"\n{'='*60}")
    print("  STARTUP PROGRAMS CHECK")
    print(f"{'='*60}")
    print("  Checking for suspicious programs that run at startup...\n")
    
    suspicious = ["keylogger", "rat", "trojan", "backdoor", "remote", "hack"]
    
    reg_paths = [
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    ]
    
    found = []
    for path in reg_paths:
        result = subprocess.run(
            f'reg query "{path}"',
            capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                line = line.strip()
                if "=" in line:
                    name = line.split("=")[0].strip()
                    value = "=".join(line.split("=")[1:]).strip()
                    
                    is_suspicious = any(s in name.lower() or s in value.lower() for s in suspicious)
                    if is_suspicious:
                        add_alert("HIGH", f"Suspicious startup: {name}")
                        found.append((name, value, "SUSPICIOUS"))
                    else:
                        found.append((name, value, "OK"))
    
    if found:
        print(f"  Found {len(found)} startup program(s):")
        for name, value, status in found:
            icon = "[!!!]" if status == "SUSPICIOUS" else "[OK]"
            print(f"    {icon} {name}")
            if status == "SUSPICIOUS":
                print(f"         {value}")
    else:
        print("  No startup programs found.")
    
    print(f"\n{'='*60}\n")


def check_email_breach():
    print(f"\n{'='*60}")
    print("  EMAIL BREACH CHECK")
    print(f"{'='*60}")
    print("  Checks if your email appeared in known data breaches.")
    print("  Uses Have I Been Pwned (safe, public database).\n")
    
    config = load_config()
    emails = []
    
    if config.get("email"):
        print(f"  Saved email: {config['email']}")
        use_saved = input("  Use this email? (y/n): ").strip().lower()
        if use_saved == "y":
            emails.append(config["email"])
    
    if not emails:
        print("  Enter email addresses to check (empty line to finish):")
        while True:
            try:
                email = input("  Email: ").strip()
                if not email:
                    break
                if "@" in email:
                    emails.append(email)
                else:
                    print("  Invalid email format.")
            except (EOFError, KeyboardInterrupt):
                break
    
    if not emails:
        print("  No emails entered.")
        return
    
    print(f"\n  Checking {len(emails)} email(s)...\n")
    
    for email in emails:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        try:
            req = urllib.request.Request(url)
            req.add_header("User", "IdentityProtectionTool")
            with urllib.request.urlopen(req, timeout=10) as response:
                breaches = json.loads(response.read().decode("utf-8"))
                print(f"  {email}: Found in {len(breaches)} breach(es)!")
                for b in breaches[:5]:
                    name = b.get("Name", "Unknown")
                    date = b.get("BreachDate", "Unknown")
                    count = b.get("PwnCount", 0)
                    print(f"    [!!!] {name} ({date}) - {count:,} accounts exposed")
                    add_alert("HIGH", f"Email found in breach: {name} ({date})")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  {email}: Not found in any breaches - good!")
            elif e.code == 401:
                print(f"  {email}: API key required for this check")
            else:
                print(f"  {email}: Could not check (error {e.code})")
        except Exception as e:
            print(f"  {email}: Could not check (network error)")
    
    print(f"\n{'='*60}\n")


def check_password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    
    labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong", "Excellent"]
    return labels[min(score, len(labels) - 1)], score


def password_strength_checker():
    print(f"\n{'='*60}")
    print("  PASSWORD STRENGTH CHECKER")
    print(f"{'='*60}\n")
    
    while True:
        try:
            pw = input("  Enter password to check (empty to finish): ").strip()
            if not pw:
                break
            
            strength, score = check_password_strength(pw)
            bar = "#" * score + "-" * (6 - score)
            print(f"  Strength: [{bar}] {strength}")
            
            if score < 4:
                add_alert("MEDIUM", f"Weak password detected")
            
            print()
        except (EOFError, KeyboardInterrupt):
            break
    
    print(f"{'='*60}\n")


def check_wifi_security():
    print(f"\n{'='*60}")
    print("  WIFI SECURITY CHECK")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        "netsh wlan show interfaces",
        capture_output=True, text=True, shell=True
    )
    
    if result.stdout:
        print(result.stdout)
        
        if "WPA" in result.stdout or "WPA2" in result.stdout or "WPA3" in result.stdout:
            print("  [OK] WiFi encryption: WPA detected (good)")
        else:
            print("  [!!!] WiFi encryption: Weak or unknown")
            add_alert("MEDIUM", "Weak WiFi encryption detected")
    else:
        print("  Could not retrieve WiFi info.")
    
    print(f"\n{'='*60}\n")


def check_browser_security():
    print(f"\n{'='*60}")
    print("  BROWSER SECURITY CHECK")
    print(f"{'='*60}\n")
    
    chrome_paths = [
        Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Preferences",
        Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/Preferences",
    ]
    
    for path in chrome_paths:
        if path.exists():
            print(f"  Found: {path.parent.parent.name}")
            try:
                data = json.loads(safe_read(path) or "{}")
                safe_browsing = data.get("safebrowsing", {}).get("enabled", None)
                if safe_browsing is not None:
                    status = "[OK] Enabled" if safe_browsing else "[!!!] Disabled"
                    print(f"    Safe Browsing: {status}")
            except:
                print("    Could not read preferences")
    
    print(f"\n{'='*60}\n")


def show_alerts():
    alerts = load_alerts()
    print(f"\n{'='*60}")
    print("  SECURITY ALERTS")
    print(f"{'='*60}\n")
    
    if not alerts:
        print("  No alerts. System looks clean.")
    else:
        high = sum(1 for a in alerts if a["severity"] == "HIGH")
        medium = sum(1 for a in alerts if a["severity"] == "MEDIUM")
        low = sum(1 for a in alerts if a["severity"] == "LOW")
        
        print(f"  Summary: {high} HIGH | {medium} MEDIUM | {low} LOW\n")
        
        for alert in alerts[-20:]:
            icon = {"HIGH": "[!!!]", "MEDIUM": "[!]", "LOW": "[i]"}[alert["severity"]]
            time = alert["time"][:19]
            print(f"  {icon} [{time}] {alert['message']}")
    
    print(f"\n{'='*60}\n")


def clear_alerts():
    save_alerts([])
    print("  Alerts cleared.")


def full_scan():
    print(f"\n{'#'*60}")
    print("  FULL IDENTITY PROTECTION SCAN")
    print(f"  Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")
    
    clear_alerts()
    
    scan_sensitive_files()
    scan_files_for_ids()
    check_network_security()
    check_usb_devices()
    check_startup_programs()
    check_wifi_security()
    check_browser_security()
    
    config = load_config()
    config["last_scan"] = datetime.datetime.now().isoformat()
    save_config(config)
    
    alerts = load_alerts()
    high = sum(1 for a in alerts if a["severity"] == "HIGH")
    medium = sum(1 for a in alerts if a["severity"] == "MEDIUM")
    
    print(f"\n{'#'*60}")
    print(f"  SCAN COMPLETE")
    print(f"  Alerts: {high} HIGH | {medium} MEDIUM")
    if high > 0:
        print("  WARNING: High severity issues found! Review alerts.")
    else:
        print("  System looks secure.")
    print(f"{'#'*60}\n")
    
    report = f"""
IDENTITY PROTECTION REPORT
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ALERTS: {high} HIGH | {medium} MEDIUM
Last Scan: {config.get('last_scan', 'N/A')}
Watched Folders: {config.get('watch_folders', [])}
"""
    safe_write(REPORT_FILE, report)
    print(f"  Report saved to: {REPORT_FILE}")


def setup_wizard():
    print(f"\n{'='*60}")
    print("  IDENTITY PROTECTION SETUP")
    print(f"{'='*60}\n")
    
    config = load_config()
    
    print("  Current watched folders:")
    for i, f in enumerate(config["watch_folders"], 1):
        print(f"    {i}. {f}")
    
    print("\n  Add a folder to watch? (path or empty to skip)")
    try:
        folder = input("  Folder path: ").strip()
        if folder and Path(folder).exists():
            if folder not in config["watch_folders"]:
                config["watch_folders"].append(folder)
                save_config(config)
                print(f"  Added: {folder}")
            else:
                print("  Already watching this folder.")
    except (EOFError, KeyboardInterrupt):
        pass
    
    print("\n  Enter your email for alerts (optional):")
    try:
        email = input("  Email: ").strip()
        if email:
            config["email"] = email
            save_config(config)
            print(f"  Saved: {email}")
    except (EOFError, KeyboardInterrupt):
        pass
    
    print(f"\n  Setup complete!")
    print(f"{'='*60}\n")


def show_help():
    print(f"""
{'='*60}
  IDENTITY PROTECTION TOOL
{'='*60}

  SECURITY SCANS
    scan           Full system scan (recommended)
    passwords      Check if passwords are leaked
    strength       Check password strength
    breaches       Check if email is in data breaches
    network        Check network security
    wifi           Check WiFi security
    usb            Check connected USB devices
    startup        Check startup programs
    browser        Check browser security

  FILE PROTECTION
    files          Scan for sensitive files
    ids            Scan files for personal data (SSN, etc.)

  ALERTS
    alerts         Show security alerts
    clear          Clear all alerts

  SETTINGS
    setup          Setup wizard (add folders, email)
    config         Show current configuration

  OTHER
    help           Show this help
    exit           Exit

{'='*60}
""")


def show_config():
    config = load_config()
    print(f"\n{'='*60}")
    print("  CONFIGURATION")
    print(f"{'='*60}")
    print(f"  Email: {config.get('email', 'Not set')}")
    print(f"  Last Scan: {config.get('last_scan', 'Never')}")
    print(f"  Watched Folders:")
    for f in config.get("watch_folders", []):
        exists = "[OK]" if Path(f).exists() else "[MISSING]"
        print(f"    {exists} {f}")
    print(f"{'='*60}\n")


def main():
    os.system("title Identity Protection Tool")
    
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        process_command(cmd)
        return
    
    print(f"\n{'='*60}")
    print("  IDENTITY PROTECTION TOOL")
    print("  Protect yourself from identity theft")
    print("  Type 'help' for commands")
    print(f"{'='*60}\n")
    
    while True:
        try:
            user_input = input("identity> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Stay safe!")
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
    elif action == "scan":
        full_scan()
    elif action == "passwords" or action == "password":
        password_checker()
    elif action == "strength":
        password_strength_checker()
    elif action == "breaches" or action == "breach":
        check_email_breach()
    elif action == "files":
        scan_sensitive_files()
    elif action == "ids":
        scan_files_for_ids()
    elif action == "network":
        check_network_security()
    elif action == "wifi":
        check_wifi_security()
    elif action == "usb":
        check_usb_devices()
    elif action == "startup":
        check_startup_programs()
    elif action == "browser":
        check_browser_security()
    elif action == "alerts":
        show_alerts()
    elif action == "clear":
        clear_alerts()
    elif action == "setup":
        setup_wizard()
    elif action == "config":
        show_config()
    else:
        print(f"Unknown command: {action}. Type 'help' for commands.")


if __name__ == "__main__":
    main()
