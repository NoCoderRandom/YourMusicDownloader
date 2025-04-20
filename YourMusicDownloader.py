import subprocess
import os
import sys
import importlib.util
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import zipfile
import io
import string

# ---------- Auto-Install Dependencies ----------
def install_if_missing(package):
    import_name = package.replace("-", "_")
    if importlib.util.find_spec(import_name) is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_if_missing("requests")

# ---------- Constants ----------
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TOOLS = {
    "yt-dlp.exe": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
    "ffmpeg.zip": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
}

# ---------- Tool Setup ----------
def ensure_tools(log):
    if not os.path.exists("yt-dlp.exe"):
        log("[INFO] Downloading yt-dlp.exe...")
        r = requests.get(TOOLS["yt-dlp.exe"])
        with open("yt-dlp.exe", "wb") as f:
            f.write(r.content)

    if not os.path.exists("ffmpeg.exe"):
        log("[INFO] Downloading and extracting ffmpeg.exe...")
        r = requests.get(TOOLS["ffmpeg.zip"])
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for file in z.namelist():
            if file.endswith("bin/ffmpeg.exe"):
                z.extract(file, ".")
                os.rename(file, "ffmpeg.exe")
                break

    log("[INFO] Tools are ready.")

# ---------- Utility ----------
def sanitize_title(title):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return ''.join(c if c in valid_chars else '_' for c in title)

# ---------- Download & Convert ----------
def search_and_download(query, log):
    log(f"[INFO] Searching YouTube for: {query}")
    result = subprocess.run(
        ["yt-dlp.exe", "--default-search", "ytsearch1", "--print", "title", query],
        capture_output=True,
        text=True
    )
    title = sanitize_title(result.stdout.strip())
    log(f"[INFO] Selected: {title}")

    output_template = os.path.join(DOWNLOAD_DIR, f"{title}.%(ext)s")

    subprocess.run([
        "yt-dlp.exe", "--default-search", "ytsearch1",
        "-o", output_template, "-f", "bestaudio+best", query
    ], check=True)

    for ext in ["webm", "mkv", "mp4"]:
        file_path = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")
        if os.path.exists(file_path):
            return file_path, title

    raise FileNotFoundError("[ERROR] Downloaded file not found.")

def convert_to_mp3(video_path, title, log):
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")
    log(f"[INFO] Converting to MP3: {mp3_path}")
    subprocess.run([
        "ffmpeg.exe", "-y", "-i", video_path, "-q:a", "0", "-map", "a", mp3_path
    ], check=True)
    log(f"[INFO] MP3 saved: {mp3_path}")
    os.remove(video_path)
    log(f"[INFO] Deleted video: {video_path}")

# ---------- GUI ----------
def run_download(query_var, log, download_button):
    def task():
        try:
            download_button.config(state="disabled")
            ensure_tools(log)
            query = query_var.get().strip()
            if not query:
                log("[ERROR] Please enter a search query.")
                return
            video_path, title = search_and_download(query, log)
            convert_to_mp3(video_path, title, log)
            messagebox.showinfo("Success", "MP3 downloaded successfully!")
            query_var.set("")  # Clear search box
        except Exception as e:
            log(f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))
        finally:
            download_button.config(state="normal")

    threading.Thread(target=task).start()

def open_downloads_folder():
    if sys.platform == "win32":
        os.startfile(DOWNLOAD_DIR)
    elif sys.platform == "darwin":
        subprocess.run(["open", DOWNLOAD_DIR])
    else:
        subprocess.run(["xdg-open", DOWNLOAD_DIR])

def create_gui():
    window = tk.Tk()
    window.title("🎵 Your Music Downloader")

    frm = ttk.Frame(window, padding=10)
    frm.grid()

    ttk.Label(frm, text="Search Music:").grid(column=0, row=0, sticky="w")
    query_var = tk.StringVar()
    search_entry = ttk.Entry(frm, width=50, textvariable=query_var)
    search_entry.grid(column=0, row=1, columnspan=3, pady=5)

    log_output = scrolledtext.ScrolledText(frm, width=60, height=15, state="disabled")
    log_output.grid(column=0, row=3, columnspan=3, pady=10)

    def log(text):
        log_output.configure(state="normal")
        log_output.insert("end", text + "\n")
        log_output.see("end")
        log_output.configure(state="disabled")

    download_button = ttk.Button(frm, text="Download MP3", command=lambda: run_download(query_var, log, download_button))
    download_button.grid(column=0, row=2, pady=5, sticky="w")

    open_button = ttk.Button(frm, text="Open Downloads Folder", command=open_downloads_folder)
    open_button.grid(column=1, row=2, pady=5)

    exit_button = ttk.Button(frm, text="Exit", command=window.destroy)
    exit_button.grid(column=2, row=2, pady=5, sticky="e")

    window.mainloop()

# ---------- Run ----------
if __name__ == "__main__":
    create_gui()
