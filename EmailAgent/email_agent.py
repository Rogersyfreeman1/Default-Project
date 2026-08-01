import imaplib
import email
from email.header import decode_header
from collections import Counter
import json
import os
import sys
import socket
from datetime import datetime, timedelta
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

YAHOO_IMAP = "imap.mail.yahoo.com"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "email_agent_report.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")


def load_credentials():
    email = os.environ.get("YAHOO_EMAIL", "")
    password = os.environ.get("YAHOO_APP_PASSWORD", "")
    if email and password:
        return email, password
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            creds = json.load(f)
        return creds.get("email", ""), creds.get("app_password", "")
    return "", ""

class UnsubscribeLinkParser(HTMLParser):
    """Extract unsubscribe links from email HTML"""
    def __init__(self):
        super().__init__()
        self.links = []
        self.in_link = False
        self.current_href = ""
    
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.current_href = value
                    self.in_link = True
    
    def handle_data(self, data):
        if self.in_link:
            text = data.lower()
            if any(word in text for word in ["unsubscribe", "opt out", "remove", "stop emails"]):
                self.links.append(self.current_href)
            self.in_link = False
            self.current_href = ""


def extract_unsubscribe_links(msg):
    """Extract unsubscribe links from email message"""
    links = []
    
    # Check List-Unsubscribe header (most reliable)
    list_unsub = msg.get("List-Unsubscribe", "")
    if list_unsub:
        url_match = re.search(r'<(https?://[^>]+)>', list_unsub)
        if url_match:
            links.append(url_match.group(1))
    
    # Check email body for unsubscribe links
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/html", "text/plain"]:
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        body_str = body.decode("utf-8", errors="ignore")
                        # Find unsubscribe links in HTML
                        parser = UnsubscribeLinkParser()
                        parser.feed(body_str)
                        links.extend(parser.links)
                        # Also find plain text URLs
                        url_matches = re.findall(r'https?://[^\s<>"]+unsubscribe[^\s<>"]*', body_str, re.IGNORECASE)
                        links.extend(url_matches)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True)
            if body:
                body_str = body.decode("utf-8", errors="ignore")
                parser = UnsubscribeLinkParser()
                parser.feed(body_str)
                links.extend(parser.links)
                url_matches = re.findall(r'https?://[^\s<>"]+unsubscribe[^\s<>"]*', body_str, re.IGNORECASE)
                links.extend(url_matches)
        except:
            pass
    
    # Deduplicate
    return list(set(links))


def unsubscribe_from_sender(url, timeout=10):
    """Visit unsubscribe URL to unsubscribe"""
    try:
        # Add common headers to look like a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            return status == 200
    except Exception as e:
        print(f"  Unsubscribe error: {e}")
        return False


def process_unsubscribes(mail, message_nums, sender_subjects, dry_run=False):
    """Process unsubscribe links for spam emails"""
    unsubscribed = 0
    failed = 0
    results = []
    
    for num in message_nums:
        try:
            # Fetch email
            status, msg_data = mail.uid("FETCH", num, "(RFC822)")
            if status != "OK":
                continue
            
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            sender = get_sender(msg)
            subject = sender_subjects.get(sender, "")
            
            # Extract unsubscribe links
            links = extract_unsubscribe_links(msg)
            
            if links:
                print(f"  Found unsubscribe link for: {sender}")
                if not dry_run:
                    for link in links:
                        if unsubscribe_from_sender(link):
                            unsubscribed += 1
                            results.append({"sender": sender, "status": "success", "url": link})
                            print(f"    Unsubscribed: {sender}")
                            break
                else:
                    print(f"    Would unsubscribe: {link}")
            else:
                print(f"  No unsubscribe link: {sender}")
                failed += 1
                
        except Exception as e:
            print(f"  Error processing {num}: {e}")
    
    return unsubscribed, failed, results


SPAM_KEYWORDS = [
    "free prize", "winner", "congratulations you", "claim your", "act now",
    "lottery", "inheritance", "urgent", "limited time", "guaranteed",
    "double your", "make money fast", "work from home", "crypto bonus",
    "bitcoin giveaway", "porn", "casino", "viagra", "replica",
    "discount code", "cash prize", "you have been selected",
    "unsubscribe", "opt out", "remove me", "stop emails",
    "special offer", "exclusive deal", "limited offer", "act fast",
    "buy now", "order now", "subscribe now", "free trial",
    "no cost", "risk free", "satisfaction guaranteed", "money back",
]

SPAM_SENDERS = [
    "noreply@", "no-reply@", "marketing@", "promo@", "offers@",
    "deals@", "sales@", "newsletter@", "info@", "hello@",
    "notifications@", "updates@", "alerts@",
    "mail@", "email@", "campaign@", "blast@", "bulk@",
    "auto@", "system@", "service@", "support@",
]

# Companies known for selling data
KNOWN_DATA_BROKERS = [
    "leadgen", "leads", "telemarketing", "solicitation",
    "advertising", "affiliate", "partner", "referral",
    "insurance", "warranty", "extended", "finance",
    "credit", "loan", "debt", "consolidation",
    "pharmacy", "supplements", "weight loss", "anti-aging",
    "dating", "singles", "match", "meet",
    "gambling", "casino", "bet", "poker",
]

BANK_SENDERS = [
    "chase.com",
]

RECENT_DAYS = 365
MAX_EMAILS = 50000
BATCH_SIZE = 100


def decode_mime_header(raw):
    if not raw:
        return ""
    parts = decode_header(raw)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                result.append(text.decode(charset or "utf-8", errors="replace"))
            except (LookupError, TypeError):
                result.append(text.decode("utf-8", errors="replace"))
        else:
            result.append(text)
    return "".join(result).strip()


def get_sender(msg):
    from_header = msg.get("From", "")
    from_decoded = decode_mime_header(from_header)
    match = re.search(r"[<]([^<>]+)[>]", from_decoded)
    if match:
        return match.group(1).lower()
    return from_decoded.lower()


def is_likely_spam_sender(sender):
    """Check if sender email looks like spam"""
    if not sender:
        return False
    sender_lower = sender.lower()
    for prefix in SPAM_SENDERS:
        if prefix in sender_lower:
            return True
    # Check for known data broker patterns
    for broker in KNOWN_DATA_BROKERS:
        if broker in sender_lower:
            return True
    return False


def load_allowed_senders():
    """Load list of approved senders (you want these emails)"""
    allowed_file = os.path.join(BASE_DIR, "allowed_senders.json")
    if os.path.exists(allowed_file):
        with open(allowed_file, "r") as f:
            return json.load(f)
    return []


def is_allowed_sender(sender):
    """Check if sender is approved"""
    allowed = load_allowed_senders()
    sender_lower = sender.lower()
    for allowed_sender in allowed:
        if allowed_sender.lower() in sender_lower:
            return True
    return False


def load_blocked_domains():
    """Load list of permanently blocked domains"""
    blocked_file = os.path.join(BASE_DIR, "blocked_domains.json")
    if os.path.exists(blocked_file):
        with open(blocked_file, "r") as f:
            return json.load(f)
    return []


def save_blocked_domain(domain):
    """Add domain to permanent block list"""
    blocked_file = os.path.join(BASE_DIR, "blocked_domains.json")
    blocked = load_blocked_domains()
    if domain not in blocked:
        blocked.append(domain)
        with open(blocked_file, "w") as f:
            json.dump(blocked, f, indent=2)
        return True
    return False


def is_blocked_domain(sender):
    """Check if sender domain is permanently blocked"""
    blocked = load_blocked_domains()
    if not blocked:
        return False
    for domain in blocked:
        if domain.lower() in sender.lower():
            return True
    return False


def save_blocked_domain(domain):
    """Add domain to permanent block list"""
    blocked_file = os.path.join(BASE_DIR, "blocked_domains.json")
    blocked = []
    if os.path.exists(blocked_file):
        with open(blocked_file, "r") as f:
            blocked = json.load(f)
    if domain not in blocked:
        blocked.append(domain)
        with open(blocked_file, "w") as f:
            json.dump(blocked, f, indent=2)
        return True
    return False


def is_bank_sender(sender):
    for bank in BANK_SENDERS:
        if bank in sender:
            return True
    return False


def log_report(report):
    report["last_run"] = datetime.now().isoformat()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def main():
    YAHOO_EMAIL, YAHOO_APP_PASSWORD = load_credentials()
    if not YAHOO_EMAIL or not YAHOO_APP_PASSWORD:
        print("ERROR: Set YAHOO_EMAIL and YAHOO_APP_PASSWORD environment variables or create credentials.json.")
        sys.exit(1)

    mail = imaplib.IMAP4_SSL(YAHOO_IMAP, 993, timeout=30)
    try:
        mail.login(YAHOO_EMAIL, YAHOO_APP_PASSWORD)
        print(f"Connected to {YAHOO_EMAIL}")
    except imaplib.IMAP4.error as e:
        print(f"Login failed: {e}")
        sys.exit(1)

    status, _ = mail.select("INBOX")
    if status != "OK":
        print("Failed to open INBOX")
        mail.logout()
        sys.exit(1)

    since_date = (datetime.now() - timedelta(days=RECENT_DAYS)).strftime("%d-%b-%Y")
    status, data = mail.uid("SEARCH", None, f'(SINCE "{since_date}")')
    if status != "OK" or not data[0]:
        print("No messages found")
        mail.logout()
        return

    ids = data[0].split()
    ids = ids[-MAX_EMAILS:]
    print(f"Scanning {len(ids)} recent emails...", flush=True)

    sender_stats = Counter()
    sender_subjects = {}
    sender_first_seen = {}

    messages = []
    for start in range(0, len(ids), BATCH_SIZE):
        batch = ids[start:start + BATCH_SIZE]
        set_str = ",".join(n.decode() if isinstance(n, bytes) else str(n) for n in batch)
        status, msg_data = mail.uid("FETCH", set_str, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if status != "OK":
            continue
        for i in range(0, len(msg_data), 2):
            if i >= len(msg_data) or not isinstance(msg_data[i], tuple):
                continue
            header = msg_data[i][0]
            raw = msg_data[i][1]
            num_match = re.match(rb"(\d+)", header)
            if not num_match:
                continue
            num = num_match.group(1)
            msg = email.message_from_bytes(raw)
            sender = get_sender(msg)
            messages.append((num, sender))
            sender_stats[sender] += 1
            if sender not in sender_subjects:
                sender_subjects[sender] = decode_mime_header(msg.get("Subject", ""))[:120]
                sender_first_seen[sender] = msg.get("Date", "unknown")
        print(f"  scanned {min(start + BATCH_SIZE, len(ids))}/{len(ids)}", flush=True)

    repeat_senders = {s: c for s, c in sender_stats.items() if c >= 3}
    spam_candidates = {}
    for sender, count in repeat_senders.items():
        spam_candidates[sender] = {
            "count": count,
            "sample_subject": sender_subjects.get(sender, ""),
            "sample_date": sender_first_seen.get(sender, ""),
        }

    # AUTO-ERASE MODE: Process all non-approved senders
    print("\n--- AUTO-ERASE: Processing unapproved senders ---", flush=True)
    
    # Get all unique senders that are not allowed
    unapproved_senders = set()
    for num, sender in messages:
        if not is_allowed_sender(sender) and not is_bank_sender(sender):
            unapproved_senders.add(sender)
    
    print(f"  Found {len(unapproved_senders)} unapproved senders", flush=True)
    
    # Unsubscribe from all unapproved senders
    nums_to_unsub = [num for num, sender in messages if not is_allowed_sender(sender) and not is_bank_sender(sender)]
    unsubscribed, unsub_failed, unsub_results = process_unsubscribes(mail, nums_to_unsub, sender_subjects)
    print(f"  Unsubscribed: {unsubscribed} | Failed: {unsub_failed}", flush=True)
    
    # Block all unapproved domains permanently
    print("\n--- Blocking unapproved domains ---", flush=True)
    blocked_count = 0
    for sender in unapproved_senders:
        if "@" in sender:
            domain = sender.split("@")[1]
            if save_blocked_domain(domain):
                blocked_count += 1
                print(f"  Blocked: {domain}")
    print(f"  Blocked {blocked_count} domains permanently", flush=True)
    
    moved = 0
    skipped = 0
    nums_to_bulk = []
    nums_to_banks = []
    bulk_details = []
    banks_details = []
    for idx, (num, sender) in enumerate(messages):
        if idx % 50 == 0:
            print(f"  checking {idx}/{len(messages)}", flush=True)
        
        # AUTO-ERASE MODE: Delete anything NOT in your allowed list
        # If sender is not approved, it's spam - unsubscribe and delete
        is_spam = (
            sender in spam_candidates or 
            is_likely_spam_sender(sender) or 
            is_blocked_domain(sender) or
            (not is_bank_sender(sender) and not is_allowed_sender(sender))
        )
        
        if is_spam:
            if is_bank_sender(sender):
                nums_to_banks.append(num)
                banks_details.append({
                    "sender": sender,
                    "subject": sender_subjects.get(sender, ""),
                })
            else:
                nums_to_bulk.append(num)
                bulk_details.append({
                    "sender": sender,
                    "subject": sender_subjects.get(sender, ""),
                })

    if nums_to_bulk:
        message_set = ",".join(n.decode() if isinstance(n, bytes) else str(n) for n in nums_to_bulk)
        print(f"Moving {len(nums_to_bulk)} spam emails to Bulk...", flush=True)
        try:
            mail.uid("COPY", message_set, '"Bulk"')
            moved += len(nums_to_bulk)
        except Exception as e:
            print(f"  copy error: {e}", flush=True)
            skipped += len(nums_to_bulk)
        try:
            mail.uid("STORE", message_set, "+FLAGS", "\\Deleted")
        except Exception as e:
            print(f"  delete flag error: {e}", flush=True)

    if nums_to_banks:
        message_set = ",".join(n.decode() if isinstance(n, bytes) else str(n) for n in nums_to_banks)
        print(f"Moving {len(nums_to_banks)} bank emails to Banks folder...", flush=True)
        try:
            mail.uid("COPY", message_set, '"Banks"')
            moved += len(nums_to_banks)
        except Exception as e:
            print(f"  copy error: {e}", flush=True)
            skipped += len(nums_to_banks)
        try:
            mail.uid("STORE", message_set, "+FLAGS", "\\Deleted")
        except Exception as e:
            print(f"  delete flag error: {e}", flush=True)

    if nums_to_bulk or nums_to_banks:
        try:
            mail.expunge()
        except Exception as e:
            print(f"  expunge error: {e}", flush=True)

    report = {
        "scanned_emails": len(ids),
        "unique_senders": len(sender_stats),
        "unapproved_senders": len(unapproved_senders),
        "repeat_senders_detected": len(spam_candidates),
        "repeat_sender_details": spam_candidates,
        "unsubscribed": unsubscribed,
        "unsub_failed": unsub_failed,
        "unsub_details": unsub_results,
        "domains_blocked": blocked_count,
        "emails_moved_to_bulk": len(nums_to_bulk),
        "bulk_details": bulk_details,
        "emails_moved_to_banks": len(nums_to_banks),
        "banks_details": banks_details,
        "emails_moved_total": moved,
    }
    log_report(report)

    print(f"\n=== AUTO-ERASE REPORT ===")
    print(f"Scanned: {len(ids)} emails")
    print(f"Unapproved senders: {len(unapproved_senders)}")
    print(f"Unsubscribed: {unsubscribed}")
    print(f"Domains blocked: {blocked_count}")
    print(f"Moved to Bulk: {len(nums_to_bulk)}")
    print(f"Bank emails saved: {len(nums_to_banks)}")
    print(f"=========================")

    if spam_candidates:
        print("\nDetected repeat senders:")
        for sender, info in spam_candidates.items():
            print(f"  - {sender} ({info['count']} emails)")

    print(f"\nReport saved to {LOG_FILE}")

    mail.logout()


if __name__ == "__main__":
    main()
