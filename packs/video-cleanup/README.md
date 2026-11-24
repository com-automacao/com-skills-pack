# Video Cleanup — a Claude plugin

Ask Claude to fix a video and it will diagnose and clean up the sound, sharpen up the picture,
and add your branding, without touching your original file.

- **Audio:** AI noise removal ([DeepFilterNet](https://github.com/Rikorose/DeepFilterNet)), rumble
  cut, voice clarity EQ, loudness to −14 LUFS for social media, mono fix for voices that drift
  between left and right or whose stereo channels cancel out. Automatically checks lip sync and reports
  before/after numbers.
- **Picture:** gentle cleanup of compression blockiness, upscaling to 1080p, sharpening and a light
  colour lift for washed-out footage. Generative AI upscalers are left out on purpose because they
  invent text and facial details.
- **Branding (optional):** logo watermark, name/title lower third in your brand colour, and an end
  card with a crossfade. It can even cut your logo out of an existing video's end card.

Built from a real clean-up of outdoor interview footage and a LinkedIn product demo.

## Will it work for me? Check these first

This plugin runs real audio/video programs **on your own computer**, so it only works when all of
these are true:

| ✅ Condition | Why it matters |
|---|---|
| You use **Claude Code** (terminal or the desktop app's Code tab) | Claude needs to run local programs. Claude chat on web/mobile can't, so the plugin is listed for Claude Code only. |
| Your computer is **Windows x64, macOS (Apple Silicon or Intel) or Linux x64/arm64** | The AI noise remover (DeepFilterNet) ships prebuilt only for these. |
| **Python 3.9+** is installed | All the tools are Python scripts. |
| **ffmpeg** is installed, or you let the setup step install it | ffmpeg does the actual audio/video processing. |
| **Internet access once**, for setup | To download DeepFilterNet (~30 MB, from its official GitHub release, checksum-verified) and numpy/Pillow from PyPI. After that everything runs offline. |
| The video is a **file on your computer** (mp4, mov, mkv…) | Nothing is uploaded anywhere; it's processed in place. A LinkedIn/YouTube link needs downloading first. |

What to expect: noisy, quiet, one-sided or echoey **speech** gets clearly better, and low-quality or
re-compressed **picture** looks noticeably cleaner. Not fixable: birdsong and other whistle-like
sounds, a voice recorded very far from the mic (it stays somewhat roomy), burned-in captions, and
detail already destroyed by heavy compression. Your original file is never changed.

## Install (Claude Code)

```bash
claude plugin marketplace add Mehdi-Ks/video-cleanup
claude plugin install video-cleanup@video-cleanup
```

Then just ask, for example: *"the audio in interview.mp4 is noisy and too quiet, can you fix it?"*
or *"clean up demo.mp4 and add our logo (logo.png) and my name, Jane Doe, Head of Sales"*.

### Requirements

| Needed | How you get it |
|---|---|
| Python 3.9+ | python.org, or your system's package manager |
| ffmpeg | `winget install Gyan.FFmpeg` · `brew install ffmpeg` · `sudo apt install ffmpeg` |
| numpy, Pillow, DeepFilterNet CLI | `python skills/video-cleanup/scripts/setup_tools.py` (Claude offers to run this the first time) |

`setup_tools.py` downloads the DeepFilterNet 0.5.6 binary for your OS from its official GitHub
release, verifies its SHA-256 checksum and stores it in `~/.video-cleanup/bin/`. Add
`--install-ffmpeg` to have it install ffmpeg via winget/brew/apt too. `--check` only reports.

Supported: Windows x64, macOS (Apple Silicon and Intel), Linux x64/arm64.
This plugin is meant for **Claude Code** (CLI or desktop app), which can run local programs.

## Use the scripts without Claude

```bash
cd skills/video-cleanup/scripts
python analyze.py "talk.mp4"                       # what's wrong with the audio
python audiofix.py "talk.mp4"                      # -> "talk - audiofix (AI DeepFilterNet).mp4"
python audiofix.py "talk.mp4" --wav-only -o clean.wav
python videofix.py "talk.mp4" --audio clean.wav --logo logo.png --logo-color white \
    --name "Jane Doe" --title "Head of Sales · Acme" --color "#1F2A5C" --endcard endcard.png
python extract_logo.py --from-video brand_video.mp4 --time -0.1 --crop 80,330,560,340
```

Run any script with `-h` for all options.

## Known limits

- Birdsong and other whistle-like sounds mostly survive, because speech denoisers treat them as
  voice-like.
- A voice recorded far from the mic stays somewhat roomy; a clip-on mic fixes this at the source.
- Burned-in captions can't be restyled, and platform-compressed downloads (LinkedIn, WhatsApp)
  improve but never match the original file.

## License

MIT for this plugin's code. DeepFilterNet is MIT/Apache-2.0 and is downloaded from its own
release; ffmpeg is installed separately under its own license.
