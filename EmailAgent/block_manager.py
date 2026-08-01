"""
Block Manager for Email Agent
Block domains permanently so they can never email you again
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOCKED_FILE = os.path.join(BASE_DIR, "blocked_domains.json")


def load_blocked():
    """Load blocked domains"""
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "r") as f:
            return json.load(f)
    return []


def save_blocked(blocked):
    """Save blocked domains"""
    with open(BLOCKED_FILE, "w") as f:
        json.dump(blocked, f, indent=2)


def block_domain(domain):
    """Add domain to block list"""
    blocked = load_blocked()
    domain = domain.lower().strip()
    if domain not in blocked:
        blocked.append(domain)
        save_blocked(blocked)
        print(f"Blocked: {domain}")
        return True
    else:
        print(f"Already blocked: {domain}")
        return False


def unblock_domain(domain):
    """Remove domain from block list"""
    blocked = load_blocked()
    domain = domain.lower().strip()
    if domain in blocked:
        blocked.remove(domain)
        save_blocked(blocked)
        print(f"Unblocked: {domain}")
        return True
    else:
        print(f"Not blocked: {domain}")
        return False


def list_blocked():
    """List all blocked domains"""
    blocked = load_blocked()
    if not blocked:
        print("No domains blocked yet.")
        return
    
    print(f"\nBlocked Domains ({len(blocked)}):")
    print("-" * 40)
    for i, domain in enumerate(blocked, 1):
        print(f"  {i}. {domain}")
    print()


def block_sender(sender_email):
    """Extract and block domain from email address"""
    if "@" in sender_email:
        domain = sender_email.split("@")[1]
        return block_domain(domain)
    return False


# Quick functions for common spam
def block_data_brokers():
    """Block common data broker domains"""
    brokers = [
        "leadgen.com", "leads.com", "telemarketing.com",
        "solicitation.com", "advertising.com", "affiliate.com",
        "partner.com", "referral.com", "marketing.com",
        "promo.com", "offers.com", "deals.com",
        "insurance.com", "warranty.com", "finance.com",
        "credit.com", "loan.com", "pharmacy.com",
        "supplements.com", "dating.com", "gambling.com",
    ]
    
    count = 0
    for broker in brokers:
        if block_domain(broker):
            count += 1
    
    print(f"Blocked {count} data broker domains")


if __name__ == "__main__":
    print("Email Block Manager")
    print("=" * 40)
    print("Commands:")
    print("  block <domain.com>   - Block a domain")
    print("  unblock <domain.com> - Unblock a domain")
    print("  list                 - View blocked domains")
    print("  brokers              - Block common data brokers")
    print()
    
    list_blocked()
