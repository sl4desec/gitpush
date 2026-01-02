import os
import sys
import subprocess
import time
import json
import tkinter as tk
from tkinter import filedialog

# Enable colors for Windows
os.system("color 0F")

CONFIG_FILE = "git_accounts.json"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    clear_screen()
    banner = r"""
   ____  ___  _____  ____   _   _  ____   _   _ 
  / ___||_ _||_   _||  _ \ | | | |/ ___| | | | |
 | |  _  | |   | |  | |_) || | | |\___ \ | |_| |
 | |_| | | |   | |  |  __/ | |_| | ___) ||  _  |
  \____||___|  |_|  |_|     \___/ |____/ |_| |_|

                       @sl4de
    """
    print(banner)
    print("\n")


def run_command(command, cwd):
    try:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            command,
            cwd=cwd,
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
    except Exception as e:
        return -1, "", str(e)


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
        return None


# --- ACCOUNT MANAGER ---


def load_accounts():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_accounts(accounts):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=4)


def add_account():
    print("\n  --- ADD NEW ACCOUNT ---")
    alias = input_clean("  Account Name (e.g. Work, Personal): ")
    if not alias:
        return
    name = input_clean("  GitHub Username: ")
    if not name:
        return
    email = input_clean("  GitHub Email: ")
    if not email:
        return

    accounts = load_accounts()
    accounts.append({"name": name, "email": email, "alias": alias})
    save_accounts(accounts)
    print("  [OK] Account saved successfully!")
    time.sleep(1)


def edit_delete_account(index):
    accounts = load_accounts()
    if index < 0 or index >= len(accounts):
        return

    acc = accounts[index]

    while True:
        print_banner()
        print(f"  --- EDIT ACCOUNT: {acc.get('alias', 'Unknown')} ---")
        print(f"  Name  : {acc.get('name', 'Unknown')}")
        print(f"  Email : {acc.get('email', 'Unknown')}")
        print("-" * 40)
        print("  [1] Edit Alias")
        print("  [2] Edit Username")
        print("  [3] Edit Email")
        print("  [4] DELETE Account")
        print("  [0] Back")

        choice = input_clean("\n  Select > ")

        if choice == "1":
            val = input_clean(f"  New Alias [{acc.get('alias')}]: ")
            if val:
                acc["alias"] = val
        elif choice == "2":
            val = input_clean(f"  New Username [{acc.get('name')}]: ")
            if val:
                acc["name"] = val
        elif choice == "3":
            val = input_clean(f"  New Email [{acc.get('email')}]: ")
            if val:
                acc["email"] = val
        elif choice == "4":
            confirm = input_clean(
                "  Are you sure you want to delete this account? (y/n): "
            )
            if confirm.lower() == "y":
                del accounts[index]
                save_accounts(accounts)
                print("  [OK] Account deleted.")
                time.sleep(1)
                return
        elif choice == "0":
            save_accounts(accounts)  # Save changes if any
            return

        save_accounts(accounts)  # Save incremental changes


def select_identity_for_push():
    """Simplified selection for the Push flow"""
    accounts = load_accounts()
    if not accounts:
        return None

    print("  --- SELECT IDENTITY ---")

    for i, acc in enumerate(accounts):
        print(f"  [{i + 1}] {acc.get('alias', 'No Alias')} ({acc.get('name')})")

    default_opt = len(accounts) + 1
    print(f"  [{default_opt}] Use Default (Global Config)")

    while True:
        choice = input_clean("\n  Select > ")
        if not choice:
            continue
        if not choice.isdigit():
            continue

        idx = int(choice)

        if 1 <= idx <= len(accounts):
            return accounts[idx - 1]
        elif idx == default_opt:
            return None  # Default
        else:
            print("  [!] Invalid selection.")


def account_management_menu():
    while True:
        print_banner()
        print("  --- MANAGE IDENTITIES ---")
        accounts = load_accounts()

        counter = 1
        if not accounts:
            print("  (No accounts saved yet)")
        else:
            for acc in accounts:
                print(
                    f"  [{counter}] {acc.get('alias', 'No Alias')} ({acc.get('name')})"
                )
                counter += 1

        new_acc_opt = counter
        print("-" * 40)
        print(f"  [{new_acc_opt}] Add New Account")
        print(f"  [0] Back to Main Menu")

        choice = input_clean("\n  Select > ")

        if not choice or not choice.isdigit():
            continue

        choice_int = int(choice)

        if choice_int == new_acc_opt:
            add_account()
        elif choice_int == 0:
            break
        elif 1 <= choice_int <= len(accounts):
            edit_delete_account(choice_int - 1)
        else:
            print("  [!] Invalid number.")
            time.sleep(1)


# --- APP LOGIC ---


def select_folder_dialog():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder_selected = filedialog.askdirectory(title="Select Project Directory")
    root.destroy()
    return folder_selected


def push_workflow():
    print_banner()
    print("  Press [ENTER] to select project directory...")
    input_clean("")

    path = select_folder_dialog()
    if not path:
        print("\n  [!] Cancelled.")
        time.sleep(1)
        return

    path = os.path.normpath(path)

    print_banner()
    print(f"  Target: {path}\n")

    # Identity Selection
    identity = select_identity_for_push()

    print_banner()
    print(f"  Target: {path}")
    if identity:
        print(f"  Identity: {identity.get('alias')} ({identity.get('name')})")
    else:
        print(f"  Identity: System Default")
    print("-" * 40 + "\n")

    msg = input_clean("  Commit Message > ")
    while not msg:
        msg = input_clean("  Commit Message > ")

    print("\n" + "-" * 40)

    # 0. Configure Identity
    if identity:
        run_command(f'git config user.name "{identity["name"]}"', path)
        run_command(f'git config user.email "{identity["email"]}"', path)

    # Security: Update .gitignore
    gitignore_path = os.path.join(path, ".gitignore")
    lines_to_add = ["git_accounts.json", "__pycache__/", "*.pyc"]
    try:
        current_content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                current_content = f.read()

        with open(gitignore_path, "a", encoding="utf-8") as f:
            for line in lines_to_add:
                if line not in current_content:
                    f.write(f"\n{line}")
    except Exception as e:
        print(f"  [!] Warning (.gitignore): {e}")

    # 1. Init
    print_status("Checking Git", "...")
    git_dir = os.path.join(path, ".git")
    if not os.path.isdir(git_dir):
        run_command("git init", path)
        print_status("Checking Git", "INIT")
        run_command("git branch -M main", path)
    else:
        print_status("Checking Git", "OK")

    # 2. Add
    print_status("Adding Files", "...")
    code, out, err = run_command("git add .", path)
    if code != 0:
        print_status("Adding Files", "ERROR")
        print(f"\n[!] Error Details:\n{err}")
        input_clean("Press Enter...")
        return
    print_status("Adding Files", "OK")

    # 3. Commit
    print_status("Committing", "...")
    code, out, err = run_command(f'git commit -m "{msg}"', path)
    if code == 0:
        print_status("Committing", "OK")
    elif "nothing to commit" in out.lower():
        print_status("Committing", "SKIP", "(No changes)")
    else:
        print_status("Committing", "ERROR")
        print(f"\n[!] Error Details:\n{out}\n{err}")

    # 4. Remote
    remote = "origin"
    print_status("Checking Remote", "...")
    code, out, err = run_command("git remote -v", path)
    if remote not in out:
        print_status("Checking Remote", "MISSING")
        print("\n  [!] Repository not linked to GitHub.")
        url = input_clean("  Paste GitHub Repo URL: ")
        if url:
            run_command(f"git remote add {remote} {url}", path)
            print_status("Checking Remote", "ADDED")
        else:
            print("  [!] No URL provided. Cannot push.")
            input_clean("Press Enter...")
            return
    else:
        print_status("Checking Remote", "OK")

    # 5. Push
    print_status("Pushing to GitHub", "...")
    branch = "main"  # Assumption; could detect current branch if needed

    code, out, err = run_command(f"git push -u {remote} {branch}", path)

    if code == 0:
        print_status("Pushing to GitHub", "DONE")
        print("\n  " + "=" * 30)
        print("      SUCCESSFULLY DEPLOYED!      ")
        print("  " + "=" * 30)
    else:
        print_status("Pushing to GitHub", "FAILED")
        print("\n  [!] Push failed.")
        if "Repository not found" in err:
            print("  Reason: Repository not found on GitHub.")
            print("  Fix: Create a generic repository on GitHub first.")
        elif "non-fast-forward" in err:
            print("  Reason: Remote has changes you don't have.")
            print("  Fix: You may need to 'git pull' first.")
        else:
            print(f"  Details:\n{err}")

    input_clean("\nPress [ENTER] to return...")


def main_menu():
    while True:
        print_banner()
        print("  [1] Push Repository")
        print("  [2] Account Management")
        print("  [3] Exit")

        choice = input_clean("\n  Select > ")

        if choice == "1":
            push_workflow()
        elif choice == "2":
            account_management_menu()
        elif choice == "3":
            clear_screen()
            sys.exit()
        else:
            pass


if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        print(f"\n[!] Critical Error: {e}")
        input()
