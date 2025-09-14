#!/usr/bin/env python3
"""
GTD Import Script for FASTGTD
Imports GTD folder structure and content into FASTGTD database via API
"""

import os
import re
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
BASE_URL = "http://localhost:8003"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTY3ODE2OTcsInN1YiI6ImQ2MmNlOGY1LTJlMzMtNDRlNC04NjBjLTE1ZjM4NzM0Y2FlZSIsImVtYWlsIjoiYmthcmpvb0BnbWFpbC5jb20ifQ.llkxwlDJ5a33GSJoGDuXLjV879VAwWvvewF9bnwwCT4"
GTD_ROOT = "/mnt/backup/GTD"

# Folder IDs (already created)
FOLDER_IDS = {
    "Home": "bdd3c130-c2ce-4644-850d-7cbb790c57bd",
    "Tariqa": "ed2817de-c24b-4bf9-879c-56bba13e4a12", 
    "Work": "c62f14e5-a956-44bb-9ae5-71802fa858bb"
}

class FastGTDImporter:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        self.stats = {
            "folders_processed": 0,
            "tasks_created": 0,
            "notes_uploaded": 0,
            "files_skipped": 0,
            "errors": []
        }

    def log(self, message: str, level: str = "INFO"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}")

    def get_folder_contents(self, parent_id: str) -> Dict:
        """Get existing folders under a parent"""
        response = requests.get(
            f"{BASE_URL}/nodes/",
            headers=self.headers,
            params={"parent_id": parent_id}
        )
        if response.status_code == 200:
            folders = {}
            for item in response.json():
                if item["node_type"] == "folder":
                    folders[item["title"]] = item["id"]
            return folders
        return {}

    def create_task(self, title: str, parent_id: str, description: str = "", 
                   status: str = "todo", completed_at: str = None, sort_order: int = 0) -> Optional[str]:
        """Create a task node"""
        task_data = {
            "description": description,
            "status": status
        }
        if completed_at:
            task_data["completed_at"] = completed_at

        data = {
            "title": title,
            "node_type": "task", 
            "parent_id": parent_id,
            "task_data": task_data,
            "sort_order": sort_order
        }

        response = requests.post(f"{BASE_URL}/nodes/", headers=self.headers, json=data)
        if response.status_code == 200:
            self.stats["tasks_created"] += 1
            return response.json()["id"]
        else:
            self.stats["errors"].append(f"Failed to create task '{title}': {response.text}")
            return None

    def create_folder(self, title: str, parent_id: str, description: str = "") -> Optional[str]:
        """Create a folder node"""
        data = {
            "title": title,
            "node_type": "folder",
            "parent_id": parent_id,
            "description": description
        }

        response = requests.post(f"{BASE_URL}/nodes/", headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            self.stats["errors"].append(f"Failed to create folder '{title}': {response.text}")
            return None

    def upload_note_file(self, file_path: str, node_id: str, title: str = None) -> Optional[str]:
        """Upload markdown file as artifact using the artifacts API"""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            self.stats["files_skipped"] += 1
            return None

        files = {"file": open(file_path, "rb")}
        data = {"node_id": node_id}

        headers_upload = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

        try:
            response = requests.post(
                f"{BASE_URL}/artifacts",
                headers=headers_upload,
                files=files,
                data=data
            )
            files["file"].close()

            if response.status_code == 201:  # artifacts endpoint returns 201
                self.stats["notes_uploaded"] += 1
                return response.json()["id"]
            else:
                self.stats["errors"].append(f"Failed to upload {file_path}: {response.text}")
                return None
        except Exception as e:
            self.stats["errors"].append(f"Error uploading {file_path}: {str(e)}")
            return None

    def parse_task_line(self, line: str) -> Tuple[str, str, bool, Optional[str]]:
        """Parse a task line and extract components"""
        line = line.strip()
        
        # Check if completed
        completed = line.startswith("- [x]")
        if not (completed or line.startswith("- [ ]")):
            return "", "", False, None

        # Remove checkbox
        content = line[5:].strip()  # Remove "- [x]" or "- [ ]"
        
        # Extract completed timestamp if present
        completed_at = None
        if "completed:" in content:
            match = re.search(r"completed:\s*([0-9-]+\s+[0-9:]+)", content)
            if match:
                try:
                    completed_at = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").isoformat() + "Z"
                except:
                    pass

        # Split title from additional info (everything after first " - ")
        parts = content.split(" - ", 1)
        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""

        return title, description, completed, completed_at

    def process_markdown_file(self, file_path: str, parent_id: str) -> List[str]:
        """Process a markdown file and extract tasks"""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return []

        created_ids = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            sort_order = 1
            for line in lines:
                title, description, completed, completed_at = self.parse_task_line(line)
                if title:
                    status = "done" if completed else "todo"
                    task_id = self.create_task(
                        title=title,
                        parent_id=parent_id,
                        description=description,
                        status=status,
                        completed_at=completed_at,
                        sort_order=sort_order
                    )
                    if task_id:
                        created_ids.append(task_id)
                    sort_order += 1

        except Exception as e:
            self.stats["errors"].append(f"Error processing {file_path}: {str(e)}")

        return created_ids

    def process_project_folder(self, project_path: str, parent_id: str, project_name: str):
        """Process a single project folder"""
        self.log(f"Processing project: {project_name}")
        
        # Process next_actions.md for tasks
        next_actions_path = os.path.join(project_path, "next_actions.md")
        if os.path.exists(next_actions_path):
            self.process_markdown_file(next_actions_path, parent_id)

        # Process time_log.md for completed tasks
        time_log_path = os.path.join(project_path, "time_log.md") 
        if os.path.exists(time_log_path):
            self.process_markdown_file(time_log_path, parent_id)

        # Process other .md files as notes (plan.md, etc)
        for file_name in ["plan.md"]:
            file_path = os.path.join(project_path, file_name)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1:
                title = file_name.replace('.md', '')
                self.upload_note_file(file_path, parent_id, title)

        # Process project_support folder if it exists
        project_support_path = os.path.join(project_path, "project_support")
        if os.path.exists(project_support_path) and os.path.isdir(project_support_path):
            # Create Project Support subfolder
            support_folder_id = self.create_folder("Project Support", parent_id)
            if support_folder_id:
                self.log(f"Created Project Support folder for {project_name}")
                
                # Upload all .md files from project_support
                for file_name in os.listdir(project_support_path):
                    if file_name.endswith('.md') and not file_name.startswith('.'):
                        file_path = os.path.join(project_support_path, file_name)
                        if os.path.getsize(file_path) > 1:  # Skip empty files
                            title = file_name.replace('.md', '')
                            self.upload_note_file(file_path, support_folder_id, title)

    def process_main_folder(self, folder_name: str):
        """Process a main folder (Home, Work, Tariqa)"""
        if folder_name not in FOLDER_IDS:
            self.log(f"Folder {folder_name} not found in FOLDER_IDS", "ERROR")
            return

        parent_id = FOLDER_IDS[folder_name]
        projects_path = os.path.join(GTD_ROOT, "projects", folder_name)
        
        if not os.path.exists(projects_path):
            self.log(f"Projects path not found: {projects_path}", "ERROR")
            return

        # Get existing subfolders
        existing_folders = self.get_folder_contents(parent_id)
        
        # Process each project subdirectory
        for project_name in os.listdir(projects_path):
            project_path = os.path.join(projects_path, project_name)
            if os.path.isdir(project_path):
                if project_name in existing_folders:
                    project_folder_id = existing_folders[project_name]
                    self.process_project_folder(project_path, project_folder_id, project_name)
                    self.stats["folders_processed"] += 1
                else:
                    self.log(f"Folder {project_name} not found in FASTGTD, skipping", "WARN")

    def import_all(self):
        """Import all GTD content"""
        self.log("Starting GTD import process")
        
        for folder_name in ["Home", "Tariqa", "Work"]:
            self.log(f"\n--- Processing {folder_name} folder ---")
            self.process_main_folder(folder_name)

        self.log("\n--- Import Summary ---")
        self.log(f"Folders processed: {self.stats['folders_processed']}")
        self.log(f"Tasks created: {self.stats['tasks_created']}")  
        self.log(f"Notes uploaded: {self.stats['notes_uploaded']}")
        self.log(f"Files skipped: {self.stats['files_skipped']}")
        self.log(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            self.log("\nErrors encountered:")
            for error in self.stats['errors']:
                self.log(f"  - {error}", "ERROR")

if __name__ == "__main__":
    importer = FastGTDImporter()
    importer.import_all()