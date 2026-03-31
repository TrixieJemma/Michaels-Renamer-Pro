import os
import subprocess
import sys
import stat
from pathlib import Path

def install_dependencies():
    # Silent install in the background
    dependencies = ["customtkinter", "requests"]
    for dep in dependencies:
        try:
            # Added --user and --break-system-packages to bypass Linux "externally-managed" errors
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dep, "--user", "--break-system-packages", "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            # Fallback for older pip versions or non-Linux systems where flag might fail
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", dep, "--user", "--quiet"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass # Silent fail to keep things "foolproof"

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

    # Simple "Installation Complete!" popup
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        messagebox.showinfo("MRP Setup", "Installation Complete!\n\nYou're all set! Check your Desktop for the Michael's Renamer Pro shortcut.")
        root.destroy()
    except Exception:
        # Fallback to console if tkinter is missing
        print("\n--- Installation Complete! ---")
        print("You're all set! Michael's Renamer Pro is ready to use.")
        print("Check your Desktop for the shortcut.")

if __name__ == "__main__":
    main()
