#!/bin/bash

echo "Starting MRP (Michael's Renamer Pro) Installer..."

# Get current directory
INSTALL_DIR=$(pwd)
APP_PATH="$INSTALL_DIR/MRP.py"
DESKTOP_PATH="$HOME/Desktop/MRP.desktop"

# Install dependencies
echo "Installing dependencies (customtkinter, requests)..."
pip install customtkinter requests --quiet

# Create the .desktop launcher
echo "Creating desktop shortcut..."
cat <<EOF > "$DESKTOP_PATH"
[Desktop Entry]
Version=1.0
Name=Michael's Renamer Pro
Comment=Manage your 40TB library with ease.
Exec=python3 "$APP_PATH"
Icon=video-x-generic
Terminal=false
Type=Application
Categories=Utility;Video;
EOF

# Make both files executable
chmod +x "$APP_PATH"
chmod +x "$DESKTOP_PATH"

echo "Success! Michael's Renamer Pro is now on your Desktop."
echo "Double-click it to start managing your library!"
