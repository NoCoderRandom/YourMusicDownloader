import subprocess
import os
import sys
import shutil
import string
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


# ---------- Constants ----------
APP_NAME = "Your Music Downloader"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
SUPPORTED_EXTENSIONS = ("webm", "mkv", "mp4", "m4a", "opus")


# ---------- Dependency Check ----------
def check_dependencies():
    """Check that yt-dlp and ffmpeg are available in PATH."""
    missing = []
    if shutil.which("yt-dlp") is None:
        missing.append("yt-dlp")
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    return missing


# ---------- Utility ----------
def sanitize_title(title):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return "".join(c if c in valid_chars else "_" for c in title).strip()


# ---------- Download & Convert ----------
def search_and_download(query, log):
    log("[INFO] Searching for: " + query)
    result = subprocess.run(
        ["yt-dlp", "--default-search", "ytsearch1", "--print", "title", query],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Search failed. Check your internet connection.")

    title = sanitize_title(result.stdout.strip())
    if not title:
        raise RuntimeError("No results found for the query.")

    log("[INFO] Found: " + title)

    output_template = os.path.join(DOWNLOAD_DIR, f"{title}.%(ext)s")
    proc = subprocess.run(
        [
            "yt-dlp",
            "--default-search", "ytsearch1",
            "-o", output_template,
            "-f", "bestaudio/best",
            query,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("Download failed: " + proc.stderr.strip())

    for ext in SUPPORTED_EXTENSIONS:
        file_path = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")
        if os.path.exists(file_path):
            return file_path, title

    raise FileNotFoundError("Downloaded file not found.")


def convert_to_mp3(video_path, title, log):
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")
    log("[INFO] Converting to MP3...")
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", mp3_path],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("Conversion failed: " + proc.stderr.strip())

    log("[INFO] Saved: " + os.path.basename(mp3_path))
    os.remove(video_path)


# ---------- GUI ----------
class MusicDownloaderApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title(APP_NAME)
        self.window.resizable(False, False)
        self.window.configure(bg="#1e1e2e")

        self._apply_style()
        self._build_ui()
        self._check_tools_on_start()

    def _apply_style(self):
        style = ttk.Style(self.window)
        style.theme_use("clam")

        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        entry_bg = "#313244"
        btn_bg = "#45475a"

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=bg, foreground=accent, font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", background=bg, foreground="#a6adc8", font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground=entry_bg, foreground=fg, insertcolor=fg)
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 6),
        )
        style.map("Accent.TButton", background=[("active", "#74c7ec"), ("disabled", "#585b70")])
        style.configure(
            "TButton",
            background=btn_bg,
            foreground=fg,
            font=("Segoe UI", 10),
            padding=(12, 6),
        )
        style.map("TButton", background=[("active", "#585b70")])

    def _build_ui(self):
        main = ttk.Frame(self.window, padding=20)
        main.grid(sticky="nsew")

        # Header
        ttk.Label(main, text=APP_NAME, style="Header.TLabel").grid(
            row=0, column=0, columnspan=3, pady=(0, 15), sticky="w"
        )

        # Search bar
        ttk.Label(main, text="Search or paste a URL:").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )

        self.query_var = tk.StringVar()
        self.search_entry = ttk.Entry(main, textvariable=self.query_var, width=55, font=("Segoe UI", 11))
        self.search_entry.grid(row=2, column=0, columnspan=3, sticky="ew", ipady=4)
        self.search_entry.bind("<Return>", lambda e: self._on_download())

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(12, 0), sticky="ew")

        self.download_btn = ttk.Button(
            btn_frame, text="Download MP3", style="Accent.TButton", command=self._on_download
        )
        self.download_btn.pack(side="left", padx=(0, 8))

        ttk.Button(btn_frame, text="Open Downloads", command=self._open_downloads).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Exit", command=self.window.destroy).pack(side="right")

        # Log area
        self.log_output = scrolledtext.ScrolledText(
            main,
            width=62,
            height=14,
            state="disabled",
            font=("Consolas", 9),
            bg="#181825",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            selectbackground="#45475a",
            borderwidth=0,
            relief="flat",
            wrap="word",
        )
        self.log_output.grid(row=4, column=0, columnspan=3, pady=(12, 0), sticky="ew")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main, textvariable=self.status_var, style="Status.TLabel").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

    def _check_tools_on_start(self):
        missing = check_dependencies()
        if missing:
            names = " and ".join(missing)
            self.log(f"[WARNING] {names} not found in PATH.")
            self.log("Please install them and ensure they are in your system PATH.")
            self.log("  yt-dlp:  https://github.com/yt-dlp/yt-dlp#installation")
            self.log("  ffmpeg:  https://ffmpeg.org/download.html")
            self.status_var.set(f"Missing: {names}")
            self.download_btn.config(state="disabled")

    def log(self, text):
        self.log_output.configure(state="normal")
        self.log_output.insert("end", text + "\n")
        self.log_output.see("end")
        self.log_output.configure(state="disabled")

    def _set_status(self, text):
        self.status_var.set(text)

    def _on_download(self):
        query = self.query_var.get().strip()
        if not query:
            self.log("[ERROR] Please enter a search query or URL.")
            return

        self.download_btn.config(state="disabled")
        self._set_status("Downloading...")
        threading.Thread(target=self._download_task, args=(query,), daemon=True).start()

    def _download_task(self, query):
        try:
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            video_path, title = search_and_download(query, self.log)
            convert_to_mp3(video_path, title, self.log)
            self.log("[DONE] Download complete!")
            self._set_status("Ready")
            self.window.after(0, lambda: self.query_var.set(""))
            self.window.after(0, lambda: messagebox.showinfo(APP_NAME, f"Downloaded: {title}.mp3"))
        except Exception as e:
            self.log(f"[ERROR] {e}")
            self._set_status("Error — see log")
            self.window.after(0, lambda: messagebox.showerror(APP_NAME, str(e)))
        finally:
            self.window.after(0, lambda: self.download_btn.config(state="normal"))

    def _open_downloads(self):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(DOWNLOAD_DIR)
        elif sys.platform == "darwin":
            subprocess.run(["open", DOWNLOAD_DIR])
        else:
            subprocess.run(["xdg-open", DOWNLOAD_DIR])

    def run(self):
        self.window.mainloop()


# ---------- Entry Point ----------
if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.run()
