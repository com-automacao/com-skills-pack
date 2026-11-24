# Privacy policy: Video Cleanup plugin

_Last updated: 3 October 2026_

**Short version: the plugin collects nothing and sends nothing. Your videos never leave your computer.**

## What the plugin does with your files

- It reads the video and audio files you point it at, **on your own computer**, using ffmpeg and
  DeepFilterNet running locally.
- It writes new output files next to the originals. It never changes, uploads or deletes your
  original files.
- Temporary working files are created in your system's temp folder and removed when each step finishes.

## What it sends over the internet

Nothing about you or your files. The plugin has no server, no analytics, no telemetry and no accounts.

The only network activity is **optional, one-time setup**, which Claude asks you before running:

| Download | From | Why |
|---|---|---|
| DeepFilterNet 0.5.6 program (~30 MB) | github.com/Rikorose/DeepFilterNet releases | AI speech noise removal; checked against a pinned SHA-256 checksum |
| numpy, Pillow | PyPI (via pip) | Python libraries the scripts use |
| ffmpeg (only with `--install-ffmpeg`) | winget / Homebrew / apt | audio/video processing |

These downloads are ordinary requests to those services and include no data from your files.

## Claude itself

The plugin runs inside Claude Code. What you type to Claude, and anything Claude reads (for example,
measurements or frames it extracts to check its work), is handled under Anthropic's own privacy
policy, not this one.

## Children

The plugin is a general-purpose tool and is not directed at children under 18.

## Contact

Questions or concerns: open an issue at https://github.com/Mehdi-Ks/video-cleanup/issues
