import os
import sys
import json
import time
import subprocess
import shutil
import tkinter as tk
import urllib.parse
from tkinter import filedialog

class ConfigManager:
    CONFIG_FILE = "git_accounts.json"

    @staticmethod
    def load_accounts():
        if not os.path.exists(ConfigManager.CONFIG_FILE):
            return []
        try:
            with open(ConfigManager.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def save_accounts(accounts):
        try:
            with open(ConfigManager.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(accounts, f, indent=4)
            return True
        except IOError:
            return False

class GitHandler:
    def __init__(self, path):
        self.path = os.path.normpath(path)

    def run(self, command, auth_identity=None, remote_name="origin"):
        original_url = None
        
        if auth_identity and auth_identity.get("token"):
            original_url = self._get_remote_url(remote_name)
            if original_url and "github.com" in original_url:
                auth_url = self._construct_auth_url(original_url, auth_identity)
                self._set_remote_url(remote_name, auth_url)

        try:
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            else:
                startupinfo = None

            process = subprocess.Popen(
                command,
                cwd=self.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                startupinfo=startupinfo,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr

        finally:
            if original_url:
                self._set_remote_url(remote_name, original_url)

    def _get_remote_url(self, remote):
        code, out, _ = self.run(f"git remote get-url {remote}")
        return out.strip() if code == 0 else None

    def _set_remote_url(self, remote, url):
        subprocess.run(
            f'git remote set-url {remote} "{url}"', 
            cwd=self.path, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def _construct_auth_url(self, original_url, identity):
        clean_url = original_url.strip()
        if clean_url.startswith("https://"):
            clean_url = clean_url.replace("https://", "")
            if "@" in clean_url:
                clean_url = clean_url.split("@")[-1]
            
            # Encode username and token to handle special chars like @ in email
            safe_user = urllib.parse.quote(identity['name'], safe='')
            safe_token = urllib.parse.quote(identity['token'], safe='')
            
            return f"https://{safe_user}:{safe_token}@{clean_url}"
        return original_url

    def get_current_branch(self):
        code, out, _ = self.run("git branch --show-current")
        if code == 0 and out.strip():
            return out.strip()
        return "main"

    def ensure_git_initialized(self):
        if not os.path.isdir(os.path.join(self.path, ".git")):
            self.run("git init")
            self.run("git branch -M main")
            return "INIT"
        
        current = self.get_current_branch()
        if not current: 
            self.run("git branch -M main")
        return "OK"

    def update_gitignore(self):
        gitignore_path = os.path.join(self.path, ".gitignore")
        lines_to_add = ["git_accounts.json", "__pycache__/", "*.pyc", ".DS_Store"]
        try:
            current_content = ""
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    current_content = f.read()
            
            with open(gitignore_path, "a", encoding="utf-8") as f:
                for line in lines_to_add:
                    if line not in current_content:
                        f.write(f"\n{line}")
        except:
            pass

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    clear_screen()
    print(r"""
   ____  ___  _____  ____   _   _  ____   _   _ 
  / ___||_ _||_   _||  _ \ | | | |/ ___| | | | |
 | |  _  | |   | |  | |_) || | | |\___ \ | |_| |
 | |_| | | |   | |  |  __/ | |_| | ___) ||  _  |
  \____||___|  |_|  |_|     \___/ |____/ |_| |_|
    """)
    print(f"{'@sl4de':^60}")
    print("\n")

def print_status(step, status, details=""):
    sys.stdout.write(f"\r  [*] {step:<30} [{status}]")
    if details:
        sys.stdout.write(f" {details}")
    sys.stdout.flush()
    if status != "...":
        print()

def input_clean(prompt):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        sys.exit()

def folder_dialog():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="Select Project Directory")
    root.destroy()
    return folder

def push_workflow():
    print_banner()
    print("  Press [ENTER] to select project directory...")
    input_clean("")
    
    path = folder_dialog()
    if not path: return

    print_banner()
    print(f"  Target: {path}\n")
    
    accounts = ConfigManager.load_accounts()
    identity = None
    if accounts:
        print("  --- SELECT IDENTITY ---")
        for i, acc in enumerate(accounts):
            print(f"  [{i+1}] {acc.get('alias')} ({acc['name']})")
        print(f"  [{len(accounts)+1}] Use System Default")
        
        sel = input_clean("\n  Select > ")
        if sel.isdigit() and 1 <= int(sel) <= len(accounts):
            identity = accounts[int(sel)-1]
            
            # Smart Token Check: If account has no token, make user enter it NOW
            if not identity.get("token"):
                print("\n  [!] Selected account has no token.")
                new_token = input_clean("  Enter GitHub Token: ")
                if new_token:
                     identity["token"] = new_token
                     # Auto-save to config
                     for acc in accounts:
                         if acc["alias"] == identity["alias"]:
                             acc["token"] = new_token
                     ConfigManager.save_accounts(accounts)
                     print("  [OK] Token saved and ready.")
                else:
                    print("  [!] Token required for push. Aborting.")
                    return

    print_banner()
    print(f"  Target: {path}")
    print(f"  User  : {identity['name'] if identity else 'System Default'}")
    print("-" * 40 + "\n")
    
    msg = input_clean("  Commit Message > ")
    while not msg: msg = input_clean("  Commit Message > ")

    print("\n" + "-" * 40)
    git = GitHandler(path)
    
    if identity:
        git.run(f'git config user.name "{identity["name"]}"')
        git.run(f'git config user.email "{identity["email"]}"')

    git.update_gitignore()

    print_status("Checking Git", "...")
    status = git.ensure_git_initialized()
    print_status("Checking Git", status)

    print_status("Adding Files", "...")
    git.run("git add .")
    print_status("Adding Files", "OK")

    print_status("Committing", "...")
    c, out, err = git.run(f'git commit -m "{msg}"')
    
    full_c_out = (out + err).lower()
    if c == 0:
         print_status("Committing", "OK")
    elif "nothing to commit" in full_c_out or "işlenecek" in full_c_out or "clean" in full_c_out:
         print_status("Committing", "SKIP", "(No changes)")
    else:
         print_status("Committing", "ERROR")

    print_status("Checking Remote", "...")
    remote_url = git._get_remote_url("origin")
    if not remote_url:
        print_status("Checking Remote", "MISSING")
        print("\n  [!] No remote 'origin' found.")
        new_url = input_clean("  Paste GitHub Repo URL: ")
        if new_url:
            git.run(f"git remote add origin {new_url}")
            print_status("Checking Remote", "ADDED")
        else:
            return
    else:
         print_status("Checking Remote", "OK")

    branch = git.get_current_branch()
    print_status(f"Pushing ({branch})", "...")
    
    c, out, err = git.run(f"git push -u origin {branch}", identity)
    
    full_output = (out + "\n" + err).lower()
    is_up_to_date = "everything up-to-date" in full_output or "her şey güncel" in full_output
    
    if c == 0 and not is_up_to_date:
        print_status("Pushing", "DONE")
        display_success()
    else:
        if "non-fast-forward" in full_output or "fetch first" in full_output or is_up_to_date:
            
            status_msg = "CONFLICT" if not is_up_to_date else "STUCK"
            print_status("Pushing", status_msg)
            
            if is_up_to_date:
                print("\n  [!] Git says 'Everything up-to-date' but you want to push.")
                print("  [!] This usually means local and remote are out of sync.")
            else:
                print("\n  [!] Remote has changes you don't have.")
            
            choice = input_clean("  [1] Pull & Merge (Safe)\n  [2] Force Push (Overwrites Remote)\n  Select > ")
            
            if choice == "1":
                print_status("Pulling", "...")
                pc, pout, perr = git.run(f"git pull origin {branch} --rebase", identity)
                if pc == 0:
                     print_status("Pulling", "OK")
                     print_status("Retrying Push", "...")
                     c, out, err = git.run(f"git push -u origin {branch}", identity)
                     if c == 0:
                         print_status("Pushing", "DONE")
                         display_success()
                         input_clean("Enter...")
                         return
                else:
                    print_status("Pulling", "FAILED")
                    git.run("git rebase --abort")
            
            elif choice == "2":
                print_status("Force Pushing", "...")
                if is_up_to_date:
                    git.run('git commit --allow-empty -m "Manual Forced Update"')
                
                c, out, err = git.run(f"git push -u origin {branch} --force", identity)
                if c == 0:
                    print_status("Force Pushing", "DONE")
                    display_success()
                    input_clean("Enter...")
                    return

        print_status("Pushing", "FAILED")
        print("\n  [Git Output]:")
        print(err)
        print(out)
    
    input_clean("\nPress [ENTER] to return...")

def account_menu():
    while True:
        print_banner()
        print("  --- ACCOUNTS ---")
        accs = ConfigManager.load_accounts()
        if not accs:
            print("  (No accounts saved)")
        
        for i, a in enumerate(accs):
            t = "****" + a.get("token", "")[-4:] if a.get("token") else "NO TOKEN"
            print(f"  [{i+1}] {a['alias']} ({a['name']}) [Token: {t}]")
        
        print("-" * 40)
        print("  [A] Add New Account")
        print("  [B] Back to Main Menu")
        
        sel = input_clean("\n  Select > ").lower()
        if sel == "b": break
        if sel == "a":
            print("\n  --- NEW ACCOUNT ---")
            alias = input_clean("  Alias (e.g. Work): ")
            name = input_clean("  Username: ")
            email = input_clean("  Email: ")
            
            token = ""
            while not token:
                token = input_clean("  Token (ghp_...) [Required]: ")
            
            if alias and name:
                accs.append({"alias":alias, "name":name, "email":email, "token":token})
                ConfigManager.save_accounts(accs) 
                print("  [OK] Saved!")
                time.sleep(1)
        
        elif sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(accs):
                while True:
                    cur = accs[idx]
                    print_banner()
                    print(f"  --- EDIT: {cur['alias']} ---")
                    print(f"  [1] Alias    : {cur.get('alias')}")
                    print(f"  [2] Username : {cur.get('name')}")
                    print(f"  [3] Email    : {cur.get('email')}")
                    t_show = "****" + cur.get('token', '')[-4:] if cur.get('token') else "Not Set"
                    print(f"  [4] Token    : {t_show}")
                    print("-" * 40)
                    print("  [5] DELETE Account")
                    print("  [0] Back")
                    
                    sub = input_clean("\n  Edit > ")
                    if sub == "0": break
                    
                    if sub == "1": cur["alias"] = input_clean(f"  New Alias [{cur['alias']}]: ") or cur["alias"]
                    if sub == "2": cur["name"] = input_clean(f"  New Username [{cur['name']}]: ") or cur["name"]
                    if sub == "3": cur["email"] = input_clean(f"  New Email [{cur['email']}]: ") or cur["email"]
                    if sub == "4": cur["token"] = input_clean(f"  New Token: ") or cur["token"]
                    if sub == "5":
                         if input_clean("  Delete? (y/n): ").lower() == "y":
                             del accs[idx]
                             break
                    ConfigManager.save_accounts(accs)

def display_success():
    print("\n  " + "="*30)
    print("      SUCCESS: SYNCED!      ")
    print("  " + "="*30)

def main():
    while True:
        print_banner()
        print("  [1] Push (Smart Sync)")
        print("  [2] Accounts")
        print("  [3] Exit")
        
        c = input_clean("\n  Select > ")
        if c == "1": push_workflow()
        elif c == "2": account_menu()
        elif c == "3": clear_screen(); sys.exit()

if __name__ == "__main__":
    main()
