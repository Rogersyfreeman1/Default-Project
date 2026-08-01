"""
GitHub Integration for Lassy AdCraft Studio
Manage repos, issues, and code from the studio
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime


class GitHubManager:
    """Connect and manage GitHub account"""

    API_URL = "https://api.github.com"

    def __init__(self):
        self.config_file = Path("github_config.json")
        self.config = self._load_config()
        self.cache_dir = Path("github_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def _load_config(self):
        """Load GitHub configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save GitHub configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _get_headers(self):
        """Get API headers"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.config.get("token"):
            headers["Authorization"] = f"token {self.config['token']}"
        return headers

    def setup(self, username=None, token=None):
        """
        Setup GitHub connection
        
        Args:
            username: GitHub username (optional for public repos)
            token: Personal access token (optional for private repos)
        
        Returns:
            True if connection successful
        """
        if username:
            self.config["username"] = username
        if token:
            self.config["token"] = token
        
        self.config["setup_date"] = datetime.now().isoformat()
        
        if self.test_connection():
            self._save_config()
            return True
        else:
            return False

    def test_connection(self):
        """Test GitHub API connection"""
        try:
            # Test with username if available
            if self.config.get("username"):
                url = f"{self.API_URL}/users/{self.config['username']}"
                response = requests.get(url, headers=self._get_headers())
                return response.status_code == 200
            
            # Test with token if available
            if self.config.get("token"):
                url = f"{self.API_URL}/user"
                response = requests.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    self.config["username"] = response.json().get("login", "")
                    return True
            
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def is_configured(self):
        """Check if GitHub is configured"""
        return bool(self.config.get("username") or self.config.get("token"))

    def get_user_info(self):
        """Get user information"""
        url = f"{self.API_URL}/users/{self.config.get('username', '')}"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code != 200:
            return None
        
        user = response.json()
        return {
            "login": user.get("login", ""),
            "name": user.get("name", ""),
            "bio": user.get("bio", ""),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "avatar_url": user.get("avatar_url", ""),
            "html_url": user.get("html_url", "")
        }

    def get_repos(self, sort="updated", per_page=30):
        """Get user repositories"""
        if self.config.get("token"):
            # Authenticated - get all repos
            url = f"{self.API_URL}/user/repos"
            params = {"sort": sort, "per_page": per_page}
        else:
            # Public only
            url = f"{self.API_URL}/users/{self.config.get('username', '')}/repos"
            params = {"sort": sort, "per_page": per_page}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code != 200:
            return []
        
        repos = []
        for repo in response.json():
            repos.append({
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "url": repo.get("html_url", ""),
                "created_at": repo.get("created_at", ""),
                "updated_at": repo.get("updated_at", ""),
                "private": repo.get("private", False)
            })
        
        return repos

    def get_repo(self, repo_name):
        """Get single repository"""
        url = f"{self.API_URL}/repos/{self.config.get('username', '')}/{repo_name}"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code != 200:
            return None
        
        repo = response.json()
        return {
            "name": repo.get("name", ""),
            "full_name": repo.get("full_name", ""),
            "description": repo.get("description", ""),
            "language": repo.get("language", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "url": repo.get("html_url", ""),
            "default_branch": repo.get("default_branch", "main"),
            "topics": repo.get("topics", [])
        }

    def get_issues(self, repo_name, state="open", per_page=30):
        """Get repository issues"""
        url = f"{self.API_URL}/repos/{self.config.get('username', '')}/{repo_name}/issues"
        params = {"state": state, "per_page": per_page}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code != 200:
            return []
        
        issues = []
        for issue in response.json():
            if "pull_request" not in issue:  # Skip PRs
                labels = [label.get("name", "") for label in issue.get("labels", [])]
                issues.append({
                    "number": issue.get("number", 0),
                    "title": issue.get("title", ""),
                    "state": issue.get("state", ""),
                    "labels": labels,
                    "created_at": issue.get("created_at", ""),
                    "url": issue.get("html_url", "")
                })
        
        return issues

    def create_issue(self, repo_name, title, body="", labels=None):
        """Create a new issue"""
        url = f"{self.API_URL}/repos/{self.config.get('username', '')}/{repo_name}/issues"
        
        payload = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        
        if response.status_code != 201:
            return None
        
        issue = response.json()
        return {
            "number": issue.get("number", 0),
            "title": issue.get("title", ""),
            "url": issue.get("html_url", "")
        }

    def get_commits(self, repo_name, per_page=10):
        """Get recent commits"""
        url = f"{self.API_URL}/repos/{self.config.get('username', '')}/{repo_name}/commits"
        params = {"per_page": per_page}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code != 200:
            return []
        
        commits = []
        for commit in response.json():
            commit_data = commit.get("commit", {})
            commits.append({
                "sha": commit.get("sha", "")[:7],
                "message": commit_data.get("message", "").split("\n")[0],
                "author": commit_data.get("author", {}).get("name", ""),
                "date": commit_data.get("author", {}).get("date", ""),
                "url": commit.get("html_url", "")
            })
        
        return commits

    def search_repos(self, query):
        """Search for repositories"""
        url = f"{self.API_URL}/search/repositories"
        params = {"q": f"{query} user:{self.config.get('username', '')}"}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        
        if response.status_code != 200:
            return []
        
        repos = []
        for repo in response.json().get("items", []):
            repos.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "url": repo.get("html_url", "")
            })
        
        return repos

    def print_user_info(self, user):
        """Print formatted user info"""
        print("\n" + "=" * 60)
        print("  GITHUB PROFILE")
        print("=" * 60)
        
        if not user:
            print("\n  User not found.")
            return
        
        print(f"\n  Username: {user['login']}")
        if user['name']:
            print(f"  Name: {user['name']}")
        if user['bio']:
            print(f"  Bio: {user['bio']}")
        print(f"  Repositories: {user['public_repos']}")
        print(f"  Followers: {user['followers']} | Following: {user['following']}")
        print(f"  Profile: {user['html_url']}")
        
        print("\n" + "=" * 60)

    def print_repos(self, repos):
        """Print formatted repo list"""
        print("\n" + "=" * 70)
        print("  YOUR REPOSITORIES")
        print("=" * 70)
        
        if not repos:
            print("\n  No repositories found.")
            return
        
        print(f"\n  Total repos: {len(repos)}\n")
        
        for i, repo in enumerate(repos, 1):
            private = "🔒" if repo["private"] else "🌐"
            print(f"  {i:2d}. {private} {repo['name']}")
            if repo['description']:
                print(f"      {repo['description'][:60]}")
            print(f"      ⭐ {repo['stars']} | 🍴 {repo['forks']} | {repo['language'] or 'N/A'}")

        print("\n" + "=" * 70)

    def print_issues(self, issues):
        """Print formatted issue list"""
        print("\n" + "=" * 70)
        print("  REPOSITORY ISSUES")
        print("=" * 70)
        
        if not issues:
            print("\n  No issues found.")
            return
        
        print(f"\n  Total issues: {len(issues)}\n")
        
        for issue in issues:
            labels = ", ".join(issue['labels']) if issue['labels'] else "none"
            print(f"  #{issue['number']}: {issue['title']}")
            print(f"    Labels: {labels} | Created: {issue['created_at'][:10]}")

        print("\n" + "=" * 70)

    def print_commits(self, commits):
        """Print formatted commit list"""
        print("\n" + "=" * 70)
        print("  RECENT COMMITS")
        print("=" * 70)
        
        if not commits:
            print("\n  No commits found.")
            return
        
        print()
        
        for commit in commits:
            print(f"  {commit['sha']} - {commit['message'][:60]}")
            print(f"    By {commit['author']} on {commit['date'][:10]}")

        print("\n" + "=" * 70)


# Quick functions
def setup_github(username=None, token=None):
    """Quick GitHub setup"""
    manager = GitHubManager()
    if manager.setup(username, token):
        print("GitHub connected successfully!")
        user = manager.get_user_info()
        manager.print_user_info(user)
        repos = manager.get_repos()
        print(f"Found {len(repos)} repositories")
        return manager
    else:
        print("Connection failed. Check your credentials.")
        return None


def quick_view_repos():
    """Quick view all repos"""
    manager = GitHubManager()
    if manager.is_configured():
        repos = manager.get_repos()
        manager.print_repos(repos)
    else:
        print("GitHub not configured. Run setup_github() first.")


if __name__ == "__main__":
    print("GitHub Integration for Lassy AdCraft Studio")
    print("=" * 50)
    
    manager = GitHubManager()
    if manager.is_configured():
        print(f"Connected as: {manager.config.get('username', 'Unknown')}")
        user = manager.get_user_info()
        manager.print_user_info(user)
        repos = manager.get_repos()
        manager.print_repos(repos)
    else:
        print("Not configured yet.")
        print("\nTo setup, run:")
        print('  setup_github("your-username")')
        print('  setup_github("your-username", "your-token")')
