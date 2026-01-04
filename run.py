#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "gitpush_app.py")
    
    try:
        result = subprocess.run([sys.executable, app_path], cwd=script_dir)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Python is installed correctly.")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
