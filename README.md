# Your Music Downloader

A desktop application for searching and downloading music as MP3 files. Built with Python and Tkinter.

## Features

- Search by song name or paste a direct URL
- Automatic conversion to high-quality MP3
- Clean, dark-themed GUI
- Downloads saved to a local `downloads/` folder

## Prerequisites

The following tools must be installed and available in your system PATH:

| Tool | Install Guide |
|------|--------------|
| **Python** 3.7+ | [python.org](https://www.python.org/downloads/) |
| **yt-dlp** | [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp#installation) |
| **ffmpeg** | [ffmpeg.org](https://ffmpeg.org/download.html) |

### Verifying installation

Open a terminal and run:

```
yt-dlp --version
ffmpeg -version
```

Both commands should print version information without errors.

## Usage

```bash
python YourMusicDownloader.py
```

1. Type a song name or paste a URL into the search bar.
2. Click **Download MP3** (or press Enter).
3. The MP3 file will appear in the `downloads/` folder.

## Platform Support

Tested on Windows 11. Should work on macOS and Linux with the prerequisites installed.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

## Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — media downloading
- [ffmpeg](https://ffmpeg.org/) — audio conversion
