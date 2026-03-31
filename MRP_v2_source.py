import os
import re
import requests
import threading
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox, Menu
import webbrowser

# === CONFIGURATION ===
MANUAL_OVERRIDES = {"ALF": 1658, "All in the Family": 1922}
TMDB_BASE_URL = "https://api.themoviedb.org/3"
VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".ts", ".m4v")

# Set theme and scale
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
# =====================

class MichaelsRenamerPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- DYNAMIC SCALING & RESPONSIVE WINDOW ---
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # 1. Scaling based on screen height
        if screen_h < 850:
            scaling = 0.85
        elif screen_h > 1200:
            scaling = 1.1
        else:
            scaling = 1.0

        ctk.set_widget_scaling(scaling)
        ctk.set_window_scaling(scaling)

        # 2. Geometry based on available space
        # We target a comfortable size but clamp it to avoid going off-screen
        win_w = min(1200, int(screen_w * 0.9))
        win_h = min(800, int(screen_h * 0.9))
        self.geometry(f"{win_w}x{win_h}")
        self.minsize(800, 600) # Ensure UI elements are always accessible
            
        self.title("MRP (Michael's Renamer Pro)")
        
        self.target_dir = ""
        self.scan_thread = None
        self.renames_data = [] # Stores file info dicts
        self.active_api_key = ""
        
        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Top Bar Config
        self.top_frame = ctk.CTkFrame(self, height=80)
        self.top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_browse = ctk.CTkButton(self.top_frame, text="Browse Folder", command=self.browse_folder, font=("Inter", 16, "bold"))
        self.btn_browse.grid(row=0, column=0, padx=20, pady=20)
        
        self.lbl_path = ctk.CTkLabel(self.top_frame, text="Waiting for Media", font=("Inter", 14))
        self.lbl_path.grid(row=0, column=1, padx=20, pady=20, sticky="w")
        
        self.btn_reset = ctk.CTkButton(self.top_frame, text="Reset", command=self.reset_app, font=("Inter", 16, "bold"), fg_color="#d9534f", hover_color="#c9302c", width=100)
        self.btn_reset.grid(row=0, column=2, padx=(20, 10), pady=20, sticky="e")
        
        self.btn_scan = ctk.CTkButton(self.top_frame, text="Scan Media", command=self.start_scan, font=("Inter", 16, "bold"), state="disabled")
        self.btn_scan.grid(row=0, column=3, padx=(10, 20), pady=20, sticky="e")
        
        # 2. Sidebar Config
        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=320)
        self.sidebar_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ns")

        ctk.CTkLabel(self.sidebar_frame, text="Server Preset", font=("Inter", 18, "bold")).grid(row=0, column=0, padx=20, pady=(20, 5))
        self.preset_var = ctk.StringVar(value="Plex")
        self.combo_preset = ctk.CTkOptionMenu(self.sidebar_frame, values=["Plex", "Jellyfin/Emby"], variable=self.preset_var, font=("Inter", 14))
        self.combo_preset.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="Manual Match (MMR)", font=("Inter", 18, "bold")).grid(row=2, column=0, padx=20, pady=(20, 5))
        
        self.entry_mmr = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Enter TMDB ID (e.g. 1658)", font=("Inter", 14))
        self.entry_mmr.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_mmr = ctk.CTkButton(self.sidebar_frame, text="Force Match", command=self.force_match, font=("Inter", 16, "bold"), fg_color="#b58d00", hover_color="#8f6f00")
        self.btn_mmr.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # TMDB Authentication Section
        self.lbl_tmdb_auth = ctk.CTkLabel(self.sidebar_frame, text="TMDB Authentication", font=("Inter", 18, "bold"))
        self.lbl_tmdb_auth.grid(row=5, column=0, padx=20, pady=(30, 5))
        
        self.entry_tmdb_key = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Paste your TMDB API Key", font=("Inter", 12), show="*")
        self.entry_tmdb_key.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        self.entry_tmdb_key.bind("<Return>", lambda event: self.verify_key_ui())

        self.context_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white")
        self.context_menu.add_command(label="Cut", command=lambda: self.entry_tmdb_key._entry.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Copy", command=lambda: self.entry_tmdb_key._entry.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Paste", command=lambda: self.entry_tmdb_key._entry.event_generate("<<Paste>>"))
        self.entry_tmdb_key.bind("<Button-3>", self.show_context_menu)
        
        self.btn_verify_key = ctk.CTkButton(self.sidebar_frame, text="Verify Key", command=self.verify_key_ui, font=("Inter", 14, "bold"))
        self.btn_verify_key.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        
        self.btn_tmdb_link = ctk.CTkButton(self.sidebar_frame, text="Get a free TMDB Key here", command=lambda: webbrowser.open("https://www.themoviedb.org/settings/api"), fg_color="transparent", text_color="#1f538d", hover_color="#gray20")
        self.btn_tmdb_link.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        # Hobbyist Personality Details
        hobbyist_text = "MRP is a labor of love for my 40TB library. This is a hobby project, not a business! If this tool helped you, consider buying me a coffee to keep the project going. I appreciate the support!"
        self.lbl_hobbyist = ctk.CTkLabel(self.sidebar_frame, text=hobbyist_text, font=("Inter", 13, "italic"), wraplength=260, justify="center", text_color="gray")
        self.lbl_hobbyist.grid(row=9, column=0, padx=20, pady=(20, 10))

        self.btn_donate = ctk.CTkButton(self.sidebar_frame, text="Buy Me a Coffee ☕", command=self.paypal_link, fg_color="#0070ba", hover_color="#00588b")
        self.btn_donate.grid(row=10, column=0, padx=20, pady=5, sticky="ew")

        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        # Apply Button at the bottom of sidebar (Never locked by quota!)
        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="APPLY CHANGES", command=self.apply_changes, 
                                       font=("Inter", 20, "bold"), fg_color="#28a745", hover_color="#218838", height=60, state="disabled")
        self.btn_apply.grid(row=12, column=0, padx=20, pady=20, sticky="ew")

        # 3. Main Content (Table)
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=0)

        # Mouse Wheel Linux Fix
        self.main_frame.bind_all("<Button-4>", lambda e: self.main_frame._parent_canvas.yview_scroll(-1, "units"))
        self.main_frame.bind_all("<Button-5>", lambda e: self.main_frame._parent_canvas.yview_scroll(1, "units"))
        
        self.load_config()
        self.setup_table_headers()

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    saved_key = data.get("api_key", "")
                    if saved_key:
                        self.entry_tmdb_key.delete(0, "end")
                        self.entry_tmdb_key.insert(0, saved_key)
                        self.validate_api_key()
            except: pass

    def save_config(self, key):
        try:
            with open("config.json", "w") as f:
                json.dump({"api_key": key}, f)
        except: pass

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def paypal_link(self):
        webbrowser.open("https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=acmike200@gmail.com&item_name=MRP+Hobby+Project+Support&currency_code=USD")

    def verify_key_ui(self):
        key = self.validate_api_key()
        if not key:
            messagebox.showwarning("Missing Key", "Please paste your TMDB API Key.")
            return
            
        # PING TMDB to confirm valid v3 key
        url = f"{TMDB_BASE_URL}/authentication/token/new?api_key={key}"
        try:
            res = requests.get(url).json()
            if res.get("success"):
                self.save_config(key)
                messagebox.showinfo("Key Verified", "TMDB API Key loaded and cleanly verified against servers. Ready to scan.")
            else:
                messagebox.showerror("Invalid Key", "TMDB rejected this API Key.\nPlease make sure you copied the small 'API Key (v3 auth)', not the massive Read Access Token.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to TMDB: {e}")

    def validate_api_key(self):
        self.active_api_key = self.entry_tmdb_key.get().strip()
        return self.active_api_key

    def setup_table_headers(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        ctk.CTkLabel(self.main_frame, text="Current Filename", font=("Inter", 16, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(self.main_frame, text="Proposed Filename", font=("Inter", 16, "bold")).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(self.main_frame, text="Status", font=("Inter", 16, "bold")).grid(row=0, column=2, padx=10, pady=10)

    def reset_app(self):
        self.target_dir = ""
        self.renames_data = []
        self.lbl_path.configure(text="Waiting for Media")
        self.setup_table_headers()
        self.btn_scan.configure(state="disabled")
        self.btn_mmr.configure(state="disabled")
        self.btn_apply.configure(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Media Folder")
        if folder:
            self.target_dir = os.path.abspath(folder)
            self.lbl_path.configure(text=f"Selected: {self.target_dir}")
            self.btn_scan.configure(state="normal")
            self.btn_mmr.configure(state="normal")

    def format_filename(self, text):
        junk_words = [r"re-dvdrip", r"redvdrip", r"360p", r"480p", r"720p", r"1080p", r"2160p", r"4k", r"x264", r"x265", r"h264", r"h265", r"web-dl", r"webrip", r"bluray", r"brrip", r"hdtv", r"proper", r"repack"]
        pattern = re.compile(r'\b(?:' + '|'.join(junk_words) + r')\b', re.IGNORECASE)
        cleaned = pattern.sub("", text)
        cleaned = cleaned.replace("re-dvdrip", "").replace("360p", "") 
        cleaned = re.sub(r"-+", "-", cleaned) 
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def clean_show_name(self, raw_name):
        name = re.sub(r"[\(\{\[].*?[\)\}\]]", "", raw_name)
        junk_words = [r"re-dvdrip", r"360p", r"480p", r"720p", r"1080p", r"2160p", r"4k", r"x264", r"x265", r"h264", r"h265", r"web-dl", r"webrip", r"bluray", r"brrip", r"hdtv", r"proper", r"repack"]
        pattern = re.compile(r'\b(?:' + '|'.join(junk_words) + r')\b', re.IGNORECASE)
        name = pattern.sub("", name)
        name = re.sub(r"[-_\.]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def fetch_show_data(self, clean_name, mmr_id=None):
        if not self.active_api_key: return None
            
        # TMDB Strict Logic
        if mmr_id:
            url = f"{TMDB_BASE_URL}/tv/{mmr_id}?api_key={self.active_api_key}"
            try:
                res = requests.get(url).json()
                if "name" in res:
                    return {"id": mmr_id, "name": res["name"], "year": res.get("first_air_date", "0000")[:4]}
            except: pass
            return None

        # Overrides Check
        for override_name, override_id in MANUAL_OVERRIDES.items():
            if override_name.lower() in clean_name.lower():
                return self.fetch_show_data(override_name, mmr_id=override_id)

        # Standard Query
        url = f"{TMDB_BASE_URL}/search/tv"
        try:
            data = requests.get(url, params={"api_key": self.active_api_key, "query": clean_name}).json()
            if data.get("results"):
                result = data["results"][0]
                return {"id": result["id"], "name": result["name"], "year": result.get("first_air_date", "0000")[:4]}
        except: pass
        return None

    def get_episode_name(self, show_info, season, episode):
        url = f"{TMDB_BASE_URL}/tv/{show_info['id']}/season/{season}/episode/{episode}?api_key={self.active_api_key}"
        try:
            data = requests.get(url).json()
            return data.get("name", f"Episode {episode}")
        except:
            return f"Episode {episode}"

    def update_ui_status(self, message):
        self.lbl_path.configure(text=message)

    def scan_operation(self, mmr_id=None):
        has_api = bool(self.validate_api_key())

        self.btn_scan.configure(state="disabled")
        self.btn_apply.configure(state="disabled")
        self.btn_mmr.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        
        self.renames_data = []
        self.after(0, self.render_table) # Clears grid visually before scan runs

        files_to_process = []
        for root, _, files in os.walk(self.target_dir):
            for filename in files:
                if filename.lower().endswith(VIDEO_EXTENSIONS) and re.search(r"S(\d+)E(\d+)", filename, re.IGNORECASE):
                    files_to_process.append((root, filename))

        total = len(files_to_process)
        if total == 0:
            self.after(0, lambda: self.update_ui_status("No valid video files found in directory."))
            self.after(0, lambda: self.reset_buttons())
            return

        for idx, (root, raw_filename) in enumerate(files_to_process):
            self.after(0, lambda m=f"Scanning {idx+1}/{total} : {raw_filename}": self.update_ui_status(m))
            
            match = re.search(r"S(\d+)E(\d+)", raw_filename, re.IGNORECASE)
            season = int(match.group(1))
            episode = int(match.group(2))
            
            raw_show_name = raw_filename[:match.start()].strip(" .-_")
            if not raw_show_name:
                raw_show_name = os.path.basename(root)
                
            clean_name = self.clean_show_name(raw_show_name)
            show_info = self.fetch_show_data(clean_name, mmr_id)
            
            old_path = os.path.abspath(os.path.join(root, raw_filename))
            ext = os.path.splitext(raw_filename)[1]
            
            if not show_info:
                # LOCAL CLEANUP MODE
                base_new = self.format_filename(f"{clean_name} - S{season:02d}E{episode:02d}")
                new_filename = f"{base_new}{ext}"
                new_filename = re.sub(r'[\\/:\*\?"<>\|]', "", new_filename)
                new_path = os.path.abspath(os.path.join(root, new_filename))
                
                status = '✅ Ready (Local)' if raw_filename != new_filename else '⚠️ Ready (Unchanged)'
                
                self.renames_data.append({
                    'old_path': old_path,
                    'new_path': new_path,
                    'old_name': raw_filename, 
                    'new_name': new_filename,
                    'status': status
                })
                continue

            ep_name = self.get_episode_name(show_info, season, episode)
            
            preset = self.preset_var.get()
            if preset == "Plex":
                raw_new_filename = f"{show_info['name']} ({show_info['year']}) {{tmdb-{show_info['id']}}} - S{season:02d}E{episode:02d} - {ep_name}"
            else:
                raw_new_filename = f"{show_info['name']} ({show_info['year']}) [tmdbid-{show_info['id']}] - S{season:02d}E{episode:02d} - {ep_name}"
            
            base_new = self.format_filename(raw_new_filename)
            new_filename = f"{base_new}{ext}"
            new_filename = re.sub(r'[\\/:\*\?"<>\|]', "", new_filename)
            new_path = os.path.abspath(os.path.join(root, new_filename))
            
            print(f"DEBUG: Raw name [{raw_filename}] vs Proposed name [{new_filename}]")
            
            if raw_filename != new_filename:
                status = '✅ Ready (TMDB)'
            else:
                status = '⚠️ Ready (Unchanged)'
            
            self.renames_data.append({
                'old_path': old_path,
                'new_path': new_path,
                'old_name': raw_filename,  
                'new_name': new_filename,
                'status': status
            })

        if not has_api:
            msg = f"No API Key: Local cleanup only. Add a TMDB key for full episode titles and IDs! ({len(self.renames_data)} analyzed)"
        else:
            msg = f"Scan complete. {len(self.renames_data)} files analyzed."
            
        self.after(0, lambda m=msg: self.update_ui_status(m))
        self.after(0, self.render_table)
        self.after(0, self.reset_buttons)

    def reset_buttons(self):
        self.btn_scan.configure(state="normal")
        self.btn_mmr.configure(state="normal")
        self.btn_browse.configure(state="normal")
        
        has_ready = any(item['status'].startswith('✅ Ready') for item in self.renames_data)
        all_unchanged = all('Unchanged' in item['status'] for item in self.renames_data)
        
        if has_ready:
            self.btn_apply.configure(state="normal")
        else:
            self.btn_apply.configure(state="disabled")
            
        if self.renames_data and all_unchanged:
            messagebox.showinfo("Library Perfect", "Everything is already perfectly named! No changes required.")

    def render_table(self):
        self.setup_table_headers()
        for idx, item in enumerate(self.renames_data):
            row = idx + 1
            color = "white"
            if item['status'].startswith('✅'): color = "#51cf66"
            elif item['status'].startswith('⚠️'): color = "#fcc419"
            elif 'Error' in item['status']: color = "#ff6b6b"

            lbl_old = ctk.CTkLabel(self.main_frame, text=item['old_name'], font=("Inter", 14), text_color="gray", wraplength=450, justify="left")
            lbl_old.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            lbl_new = ctk.CTkLabel(self.main_frame, text=item['new_name'], font=("Inter", 14), text_color=color, wraplength=450, justify="left")
            lbl_new.grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            lbl_status = ctk.CTkLabel(self.main_frame, text=item['status'], font=("Inter", 16), text_color=color)
            lbl_status.grid(row=row, column=2, padx=10, pady=5)

    def start_scan(self):
        if not self.target_dir: return
        self.scan_thread = threading.Thread(target=self.scan_operation)
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def force_match(self):
        if not self.target_dir: return
        mmr_id = self.entry_mmr.get().strip()
        if not mmr_id.isdigit():
            messagebox.showerror("Error", "TMDB ID must be numeric.")
            return
        self.scan_thread = threading.Thread(target=self.scan_operation, args=(int(mmr_id),))
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def apply_changes(self):
        if not self.renames_data: return
        
        self.btn_apply.configure(state="disabled")
        success_count = 0
        error_count = 0
        
        for item in self.renames_data:
            if item['status'].startswith('✅ Ready') and item['new_path'] and item['new_path'] != item['old_path']:
                try:
                    os.rename(item['old_path'], item['new_path'])
                    success_count += 1
                except Exception as e:
                    print(f"Error renaming {item['old_path']}: {e}")
                    error_count += 1

        msg = f"MRP Operation Completed.\n\nSuccessfully renamed: {success_count} files"
        if error_count > 0:
             msg += f"\nFailed to rename: {error_count} files"
             
        messagebox.showinfo("Apply Changes Complete", msg)
        
        self.renames_data = []
        self.render_table()
        self.update_ui_status(f"Selected: {self.target_dir}")
        self.btn_apply.configure(state="disabled")

if __name__ == "__main__":
    app = MichaelsRenamerPro()
    app.mainloop()
