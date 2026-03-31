import os
import subprocess
import sys
import stat
from pathlib import Path

def install_dependencies():
    print("--- Installing Dependencies ---")
    dependencies = ["customtkinter", "requests"]
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
        except subprocess.CalledProcessError:
            print(f"Error: Failed to install {dep}. Please run 'pip install {dep}' manually.")

def create_desktop_shortcut(app_path):
    print("--- Creating Desktop Shortcut ---")
    desktop_path = Path.home() / "Desktop" / "MRP.desktop"
    
    shortcut_content = f"""[Desktop Entry]
Version=1.0
Name=Michael's Renamer Pro
Comment=Manage your 40TB library with ease.
Exec={sys.executable} "{app_path}"
Icon=video-x-generic
Terminal=false
Type=Application
Categories=Utility;Video;
"""
    try:
        with open(desktop_path, "w") as f:
            f.write(shortcut_content)
        
        # Set desktop shortcut permissions
        st = os.stat(desktop_path)
        os.chmod(desktop_path, st.st_mode | stat.S_IEXEC)
        print(f"Success! Shortcut created at {desktop_path}")
    except Exception as e:
        print(f"Error creating shortcut: {e}")

def set_file_permissions(app_path):
    print("--- Setting File Permissions ---")
    try:
        st = os.stat(app_path)
        os.chmod(app_path, st.st_mode | stat.S_IEXEC)
        print(f"Success! Set execution permissions for {app_path}")
    except Exception as e:
        print(f"Error setting permissions: {e}")

def main():
    print("Starting MRP (Michael's Renamer Pro) Setup...")
    
    # Get the absolute path of MRP.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "MRP.py")
    
    if not os.path.exists(app_path):
        print(f"Error: Could not find MRP.py in {current_dir}. Please run setup.py from the same folder.")
        return

    install_dependencies()
    create_desktop_shortcut(app_path)
    set_file_permissions(app_path)
    
    print("\nSetup Complete!")
    print("--- Michael's Renamer Pro is ready to use! ---")
    print("You can find the shortcut on your Desktop.")

if __name__ == "__main__":
    main()
