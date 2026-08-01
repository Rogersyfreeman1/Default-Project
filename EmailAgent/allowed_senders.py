"""
Allowed Senders Manager
Add senders you WANT to receive emails from
Only these senders will be allowed - everything else gets deleted
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_FILE = os.path.join(BASE_DIR, "allowed_senders.json")


def load_allowed():
    """Load allowed senders"""
    if os.path.exists(ALLOWED_FILE):
        with open(ALLOWED_FILE, "r") as f:
            return json.load(f)
    return []


def save_allowed(allowed):
    """Save allowed senders"""
    with open(ALLOWED_FILE, "w") as f:
        json.dump(allowed, f, indent=2)


def allow_sender(sender):
    """Add sender to allowed list"""
    allowed = load_allowed()
    sender = sender.lower().strip()
    if sender not in allowed:
        allowed.append(sender)
        save_allowed(allowed)
        print(f"Allowed: {sender}")
        return True
    else:
        print(f"Already allowed: {sender}")
        return False


def disallow_sender(sender):
    """Remove sender from allowed list"""
    allowed = load_allowed()
    sender = sender.lower().strip()
    if sender in allowed:
        allowed.remove(sender)
        save_allowed(allowed)
        print(f"Removed from allowed: {sender}")
        return True
    else:
        print(f"Not in allowed list: {sender}")
        return False


def list_allowed():
    """List all allowed senders"""
    allowed = load_allowed()
    if not allowed:
        print("No senders in allowed list.")
        print("All emails from unknown senders will be deleted.")
        return
    
    print(f"\nAllowed Senders ({len(allowed)}):")
    print("-" * 40)
    for i, sender in enumerate(allowed, 1):
        print(f"  {i}. {sender}")
    print()


def add_common_senders():
    """Add common legitimate senders you want to keep"""
    common = [
        # Banks
        "chase.com", "bankofamerica.com", "wellsfargo.com", "citi.com",
        # Work
        "linkedin.com", "indeed.com", "glassdoor.com",
        # Shopping
        "amazon.com", "ebay.com", "paypal.com", "target.com", "walmart.com",
        # Services
        "apple.com", "microsoft.com", "google.com", "youtube.com",
        "netflix.com", "spotify.com", "dropbox.com",
        # Social
        "facebook.com", "instagram.com", "twitter.com", "tiktok.com",
        # Delivery
        "ups.com", "fedex.com", "usps.com",
        # Utilities
        "gmail.com", "outlook.com", "yahoo.com",
    ]
    
    count = 0
    for sender in common:
        if allow_sender(sender):
            count += 1
    
    print(f"Added {count} common senders")


if __name__ == "__main__":
    print("Allowed Senders Manager")
    print("=" * 40)
    print("Only senders in this list can email you.")
    print("Everything else gets auto-erased!")
    print()
    print("Commands:")
    print("  allow <email>     - Allow a sender")
    print("  disallow <email>  - Remove from allowed")
    print("  list              - View allowed senders")
    print("  common            - Add common legitimate senders")
    print()
    
    list_allowed()
