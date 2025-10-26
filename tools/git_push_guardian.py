#!/usr/bin/env python3
"""
🔁 SAFELOGIC SmartOrder PRO — Git Push Guardian
Auto-sync bidirectionnel GitHub toutes les 5 minutes
"""

import os
import time
import subprocess
import json
from datetime import datetime

# Configuration depuis .env
AUTO_SYNC_ENABLED = os.getenv("AUTO_SYNC_ENABLED", "true").lower() == "true"
GITHUB_REPO = os.getenv("GITHUB_REPO", "https://github.com/sazhjigbs/smartorder-pro-ai-v1.7.git")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "300"))  # 5 minutes

def log_sync(message):
    """Log sync operations"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
    # Windows-compatible log path
    try:
        log_dir = "C:\\smartorder-pro\\logs"
        os.makedirs(log_dir, exist_ok=True)
        with open(f"{log_dir}\\git_sync.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        # Fallback to local
        with open("git_sync.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

def run_git_command(cmd, cwd=None):
    """Execute git command safely"""
    try:
        # Use full Git path from D:\Git\cmd
        git_exe = "D:\\Git\\cmd\\git.exe"
        if not os.path.exists(git_exe):
            git_exe = "git"  # fallback
        
        full_cmd = f'"{git_exe}" {cmd}'
        result = subprocess.run(full_cmd, shell=True, cwd=cwd, 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Git command timeout"
    except Exception as e:
        return False, str(e)

def check_git_status():
    """Check git status and changes"""
    success, output = run_git_command("status --porcelain")
    if success:
        changes = output.strip()
        return len(changes) > 0, changes
    return False, "Git status failed"

def pull_from_github():
    """Pull latest changes from GitHub"""
    log_sync("🔄 Pulling from GitHub...")
    success, output = run_git_command(f"pull origin {GITHUB_BRANCH}")
    if success:
        log_sync(f"✅ Pull successful: {output}")
        return True
    else:
        log_sync(f"❌ Pull failed: {output}")
        return False

def push_to_github():
    """Push local changes to GitHub"""
    log_sync("📤 Pushing to GitHub...")
    
    # Add all changes
    success, output = run_git_command("add .")
    if not success:
        log_sync(f"❌ Git add failed: {output}")
        return False
    
    # Commit with auto-generated message
    commit_msg = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_git_command(f'commit -m "{commit_msg}"')
    if not success and "nothing to commit" not in output:
        log_sync(f"❌ Commit failed: {output}")
        return False
    
    # Push to GitHub
    success, output = run_git_command(f"push origin {GITHUB_BRANCH}")
    if success:
        log_sync(f"✅ Push successful: {output}")
        return True
    else:
        log_sync(f"❌ Push failed: {output}")
        return False

def sync_cycle():
    """Complete sync cycle: pull + push if needed"""
    if not AUTO_SYNC_ENABLED:
        log_sync("⏸️ Auto-sync disabled in .env")
        return
    
    log_sync("🚀 Starting sync cycle...")
    
    # 1. Pull latest changes first
    pull_success = pull_from_github()
    
    # 2. Check for local changes
    has_changes, changes = check_git_status()
    
    if has_changes:
        log_sync(f"📝 Local changes detected:\n{changes}")
        push_success = push_to_github()
        if push_success:
            log_sync("✅ Sync cycle complete - changes pushed")
        else:
            log_sync("⚠️ Sync cycle partial - push failed")
    else:
        log_sync("✅ Sync cycle complete - no local changes")

def main():
    """Main guardian loop"""
    log_sync("🛡️ Git Push Guardian started")
    log_sync(f"📁 Repo: {GITHUB_REPO}")
    log_sync(f"🌿 Branch: {GITHUB_BRANCH}")
    log_sync(f"⏱️ Interval: {SYNC_INTERVAL}s")
    
    while True:
        try:
            sync_cycle()
        except Exception as e:
            log_sync(f"💥 Sync error: {str(e)}")
        
        # Wait for next cycle
        time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    main()