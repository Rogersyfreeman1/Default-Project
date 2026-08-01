"""
Notion Integration for Lassy AdCraft Studio
Sync tasks, projects, and ideas with Notion
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime


class NotionManager:
    """Connect and sync with Notion workspace"""

    API_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"

    def __init__(self):
        self.config_file = Path("notion_config.json")
        self.config = self._load_config()
        self.cache_dir = Path("notion_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def _load_config(self):
        """Load Notion configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save Notion configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _get_headers(self):
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.config['token']}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json"
        }

    def setup(self, token):
        """
        Setup Notion connection
        
        Args:
            token: Notion integration token (starts with ntn_)
        
        Returns:
            True if connection successful
        """
        self.config["token"] = token
        self.config["setup_date"] = datetime.now().isoformat()
        
        # Test connection
        if self.test_connection():
            self._save_config()
            return True
        else:
            self.config = {}
            return False

    def test_connection(self):
        """Test Notion API connection"""
        if not self.config.get("token"):
            return False

        try:
            url = f"{self.BASE_URL}/search"
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json={"page_size": 1})
            return response.status_code == 200
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def is_configured(self):
        """Check if Notion is configured"""
        return bool(self.config.get("token"))

    def search_pages(self, query="", page_size=20):
        """Search for pages in Notion"""
        url = f"{self.BASE_URL}/search"
        headers = self._get_headers()
        
        payload = {"page_size": page_size}
        if query:
            payload["query"] = query
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Search failed: {response.status_code}")
        
        results = response.json().get("results", [])
        pages = []
        
        for page in results:
            page_info = self._parse_page(page)
            if page_info:
                pages.append(page_info)
        
        return pages

    def _parse_page(self, page):
        """Parse a Notion page object"""
        try:
            page_id = page.get("id", "")
            icon = page.get("icon", {})
            icon_emoji = icon.get("emoji", "") if icon else ""
            
            # Get title
            title = ""
            properties = page.get("properties", {})
            
            # Try different title property names
            for prop_name in ["title", "Title", "Name", "name"]:
                if prop_name in properties:
                    title_prop = properties[prop_name]
                    if title_prop.get("type") == "title":
                        title_parts = title_prop.get("title", [])
                        title = "".join(t.get("plain_text", "") for t in title_parts)
                        break
            
            if not title:
                # Try to get title from child pages
                child_title = page.get("child_page", {}).get("title", "")
                if child_title:
                    title = child_title
            
            # Get URL
            url = page.get("url", "")
            
            # Get last edited time
            last_edited = page.get("last_edited_time", "")
            
            return {
                "id": page_id,
                "title": title or "Untitled",
                "icon": icon_emoji,
                "url": url,
                "last_edited": last_edited,
                "type": page.get("object", "page")
            }
        except Exception as e:
            return None

    def get_databases(self):
        """Get all databases in workspace"""
        url = f"{self.BASE_URL}/search"
        headers = self._get_headers()
        
        payload = {
            "filter": {"value": "database", "property": "object"},
            "page_size": 100
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get databases: {response.status_code}")
        
        results = response.json().get("results", [])
        databases = []
        
        for db in results:
            title = ""
            title_prop = db.get("title", [])
            if title_prop:
                title = "".join(t.get("plain_text", "") for t in title_prop)
            
            databases.append({
                "id": db["id"],
                "title": title or "Untitled Database",
                "url": db.get("url", ""),
                "last_edited": db.get("last_edited_time", "")
            })
        
        return databases

    def get_database_items(self, database_id, page_size=50):
        """Get items from a database"""
        url = f"{self.BASE_URL}/databases/{database_id}/query"
        headers = self._get_headers()
        
        payload = {"page_size": page_size}
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get database items: {response.status_code}")
        
        results = response.json().get("results", [])
        items = []
        
        for item in results:
            parsed = self._parse_database_item(item)
            if parsed:
                items.append(parsed)
        
        return items

    def _parse_database_item(self, item):
        """Parse a database item"""
        try:
            properties = item.get("properties", {})
            
            # Get title
            title = ""
            status = ""
            priority = ""
            due_date = ""
            
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get("type", "")
                
                # Title
                if prop_type == "title":
                    title_parts = prop_data.get("title", [])
                    title = "".join(t.get("plain_text", "") for t in title_parts)
                
                # Status
                elif prop_type == "status":
                    status_obj = prop_data.get("status", {})
                    status = status_obj.get("name", "") if status_obj else ""
                
                # Select
                elif prop_type == "select":
                    select_obj = prop_data.get("select", {})
                    if select_obj:
                        if "status" in prop_name.lower():
                            status = select_obj.get("name", "")
                        elif "priority" in prop_name.lower():
                            priority = select_obj.get("name", "")
                
                # Date
                elif prop_type == "date":
                    date_obj = prop_data.get("date", {})
                    if date_obj:
                        due_date = date_obj.get("start", "")
            
            return {
                "id": item["id"],
                "title": title or "Untitled",
                "status": status,
                "priority": priority,
                "due_date": due_date,
                "url": item.get("url", ""),
                "last_edited": item.get("last_edited_time", "")
            }
        except Exception as e:
            return None

    def create_page(self, parent_id, title, content="", page_type="page"):
        """
        Create a new page in Notion
        
        Args:
            parent_id: Parent page/database ID
            title: Page title
            content: Page content (plain text)
            page_type: "page" or "database"
        
        Returns:
            Created page info
        """
        url = f"{self.BASE_URL}/pages"
        headers = self._get_headers()
        
        # Build page content
        children = []
        if content:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })
        
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": [{"text": {"content": title}}]
            }
        }
        
        if children:
            payload["children"] = children
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create page: {response.status_code}")
        
        result = response.json()
        return {
            "id": result["id"],
            "title": title,
            "url": result.get("url", "")
        }

    def add_task(self, database_id, title, status="Not started", priority="", due_date=""):
        """
        Add a task to a database
        
        Args:
            database_id: Database ID
            title: Task title
            status: Task status
            priority: Task priority
            due_date: Due date (YYYY-MM-DD)
        
        Returns:
            Created task info
        """
        url = f"{self.BASE_URL}/pages"
        headers = self._get_headers()
        
        properties = {
            "title": [{"text": {"content": title}}]
        }
        
        # Add status if database has it
        if status:
            properties["Status"] = {"status": {"name": status}}
        
        # Add priority if database has it
        if priority:
            properties["Priority"] = {"select": {"name": priority}}
        
        # Add due date if database has it
        if due_date:
            properties["Due date"] = {"date": {"start": due_date}}
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to add task: {response.status_code}")
        
        result = response.json()
        return {
            "id": result["id"],
            "title": title,
            "url": result.get("url", "")
        }

    def update_task_status(self, page_id, status):
        """Update task status"""
        url = f"{self.BASE_URL}/pages/{page_id}"
        headers = self._get_headers()
        
        payload = {
            "properties": {
                "Status": {"status": {"name": status}}
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code == 200

    def print_pages(self, pages):
        """Print formatted page list"""
        print("\n" + "=" * 70)
        print("  NOTION PAGES")
        print("=" * 70)
        
        if not pages:
            print("\n  No pages found.")
            print("  Make sure you've shared pages with the AdStudio integration.")
            return
        
        print(f"\n  Total pages: {len(pages)}\n")
        
        for i, page in enumerate(pages, 1):
            icon = page['icon'] or "📄"
            print(f"  {i:2d}. {icon} {page['title']}")
            print(f"      URL: {page['url']}")

        print("\n" + "=" * 70)

    def print_databases(self, databases):
        """Print formatted database list"""
        print("\n" + "=" * 70)
        print("  NOTION DATABASES")
        print("=" * 70)
        
        if not databases:
            print("\n  No databases found.")
            print("  Make sure you've shared databases with the AdStudio integration.")
            return
        
        print(f"\n  Total databases: {len(databases)}\n")
        
        for i, db in enumerate(databases, 1):
            print(f"  {i:2d}. 📊 {db['title']}")
            print(f"      ID: {db['id']}")
            print(f"      URL: {db['url']}")

        print("\n" + "=" * 70)

    def print_tasks(self, tasks):
        """Print formatted task list"""
        print("\n" + "=" * 70)
        print("  NOTION TASKS")
        print("=" * 70)
        
        if not tasks:
            print("\n  No tasks found.")
            return
        
        print(f"\n  Total tasks: {len(tasks)}\n")
        
        status_icons = {
            "Not started": "⬜",
            "In progress": "🔄",
            "Done": "✅",
            "Completed": "✅"
        }
        
        for i, task in enumerate(tasks, 1):
            icon = status_icons.get(task.get('status', ''), '⬜')
            print(f"  {i:2d}. {icon} {task['title']}")
            if task.get('status'):
                print(f"      Status: {task['status']}")
            if task.get('priority'):
                print(f"      Priority: {task['priority']}")
            if task.get('due_date'):
                print(f"      Due: {task['due_date']}")

        print("\n" + "=" * 70)


# Quick functions
def setup_notion(token):
    """Quick Notion setup"""
    manager = NotionManager()
    if manager.setup(token):
        print("Notion connected successfully!")
        pages = manager.search_pages()
        print(f"Found {len(pages)} pages")
        return manager
    else:
        print("Connection failed. Check your token.")
        return None


def quick_add_task(database_id, title):
    """Quick add task to database"""
    manager = NotionManager()
    if manager.is_configured():
        return manager.add_task(database_id, title)
    else:
        print("Notion not configured. Run setup_notion() first.")
        return None


if __name__ == "__main__":
    print("Notion Integration for Lassy AdCraft Studio")
    print("=" * 50)
    
    manager = NotionManager()
    if manager.is_configured():
        print("Notion is connected!")
        pages = manager.search_pages()
        manager.print_pages(pages)
    else:
        print("Not configured yet.")
        print("\nTo setup, run:")
        print('  setup_notion("your-token-here")')
