import yt_dlp
import sys
import argparse
import time
import re
import validators  # pip install validators

# ----------- Download Progress Bar -----------
def download_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
        downloaded = d.get('downloaded_bytes', 0)
        percent = downloaded / total * 100 if total else 0
        bar_len = 40
        filled_len = int(bar_len * percent // 100)
        bar = '█' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write(f'\r📥 Downloading: |{bar}| {percent:6.2f}% ')
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write('\n✅ Download complete.\n')

# ----------- Conversion Progress (Manual) -----------
def show_conversion_bar():
    bar_len = 40
    print("🎧 Converting to audio format...")
    for i in range(bar_len + 1):
        bar = '█' * i + '-' * (bar_len - i)
        percent = i / bar_len * 100
        sys.stdout.write(f'\r🎧 Conversion: |{bar}| {percent:6.2f}% ')
        sys.stdout.flush()
        time.sleep(0.03)
    sys.stdout.write('\n✅ Conversion finished!\n')

# ----------- Validation Helpers -----------
def is_valid_url(url):
    if not validators.url(url):
        return False
    supported_domains = ['youtube.com', 'youtu.be', 'tiktok.com']
    return any(domain in url for domain in supported_domains)

# ----------- Prompt Helpers -----------
def prompt_mode():
    print("\n🎬 Choose download mode:")
    options = {'1': 'audio', '2': 'video'}
    for k, v in options.items():
        print(f"  [{k}] {v}")
    while True:
        choice = input("➡️ Select mode (1–2): ").strip()
        if choice in options:
            return options[choice]
        print("❌ Invalid choice. Try again.")

def prompt_format():
    print("\n🎵 Choose audio format:")
    options = ['mp3', 'aac', 'm4a', 'opus', 'flac', 'wav']
    for i, fmt in enumerate(options, 1):
        print(f"  [{i}] {fmt}")
    while True:
        choice = input(f"➡️ Select format (1–{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice)-1]
        print("❌ Invalid choice. Try again.")

def prompt_bitrate():
    print("\n🎚 Choose an audio bitrate:")
    options = {'1': '128', '2': '192', '3': '256', '4': '320'}
    for k, v in options.items():
        print(f"  [{k}] {v} kbps")
    while True:
        choice = input("➡️ Select bitrate (1–4): ").strip()
        if choice in options:
            return options[choice]
        print("❌ Invalid choice. Try again.")

def prompt_resolution(available_resolutions):
    print("\n📺 Choose video resolution:")
    def res_key(r):
        match = re.search(r'(\d+)', r)
        return int(match.group(1)) if match else 0
    sorted_res = sorted(available_resolutions, key=res_key, reverse=True)
    for i, res in enumerate(sorted_res, 1):
        print(f"  [{i}] {res}")
    while True:
        choice = input(f"➡️ Select resolution (1–{len(sorted_res)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(sorted_res):
            return sorted_res[int(choice)-1]
        print("❌ Invalid choice. Try again.")

# ----------- Main Download Functions -----------
def download_audio(url, codec='mp3', bitrate='192', output_path='.'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [download_hook],
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': bitrate,
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    show_conversion_bar()

def download_video(url, resolution=None, output_path='.'):
    format_str = 'bestvideo+bestaudio/best'
    if resolution:
        match = re.search(r'(\d+)', resolution)
        if match:
            height = match.group(1)
            format_str = f'bestvideo[height={height}]+bestaudio/best'

    ydl_opts = {
        'format': format_str,
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [download_hook],
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# ----------- CLI ARGUMENTS -----------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download YouTube or TikTok audio/video with format/bitrate/resolution selection.",
        epilog="Examples:\n"
               "  python yt_audio.py -v dQw4w9WgXcQ -m audio\n"
               "  python yt_audio.py -y https://youtu.be/dQw4w9WgXcQ -f opus -b 256\n"
               "  python yt_audio.py -t https://www.tiktok.com/@user/video/123456789 -m video\n",
        formatter_class=argparse.RawTextHelpFormatter
    )

    group_url = parser.add_mutually_exclusive_group()
    group_url.add_argument('-y', '--youtube', type=str,
                           help='Full YouTube URL (e.g., https://www.youtube.com/watch?v=abc123)')
    group_url.add_argument('-v', '--video', type=str,
                           help='YouTube Video ID only (e.g., abc123 — the part after v=)')
    group_url.add_argument('-t', '--tiktok', type=str,
                           help='Full TikTok video URL')

    parser.add_argument('-m', '--mode', type=str,
                        choices=['audio', 'video'],
                        help='Download mode: audio or video')
    parser.add_argument('-f', '--format', type=str,
                        choices=['mp3', 'aac', 'm4a', 'opus', 'flac', 'wav'],
                        help='Audio output format (default: mp3)')
    parser.add_argument('-b', '--bitrate', type=str,
                        help='Audio bitrate (e.g., 128, 192, 256, 320 kbps)')
    parser.add_argument('-r', '--resolution', type=str,
                        help='Video resolution (e.g., 1080p, 720p). Will prompt if not supplied and mode=video.')

    args = parser.parse_args()

    # ----------- Handle URL -----------
    if args.youtube:
        url = args.youtube
    elif args.video:
        url = f"https://www.youtube.com/watch?v={args.video}"
    elif args.tiktok:
        url = args.tiktok
    else:
        # Prompt user to select platform first
        while True:
            print("\nSelect platform:")
            print("  [1] YouTube")
            print("  [2] TikTok")
            choice = input("➡️ Select (1 or 2): ").strip()
            if choice == '1':
                platform = 'youtube'
                break
            elif choice == '2':
                platform = 'tiktok'
                break
            else:
                print("❌ Invalid choice. Try again.")

        while True:
            if platform == 'youtube':
                user_input = input("🔗 Enter YouTube video URL or video ID: ").strip()
                if user_input.startswith('http'):
                    url = user_input
                else:
                    url = f"https://www.youtube.com/watch?v={user_input}"
            else:  # TikTok
                url = input("🔗 Enter full TikTok video URL: ").strip()

            if is_valid_url(url):
                break
            print("❌ Invalid URL. Press R to retry or any other key to exit.")
            choice = input().strip().lower()
            if choice != 'r':
                print("Exiting.")
                sys.exit(1)

    # ----------- Handle Mode -----------
    mode = args.mode
    if not mode:
        mode = prompt_mode()

    # ----------- Handle Audio Params -----------
    if mode == 'audio':
        codec = args.format if args.format else prompt_format()
        bitrate = args.bitrate if args.bitrate else prompt_bitrate()
        download_audio(url, codec=codec, bitrate=bitrate)

    # ----------- Handle Video Params -----------
    else:
        resolution = args.resolution
        if not resolution:
            print("Fetching available video resolutions...")
            ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    print(f"❌ Failed to retrieve video info: {e}")
                    sys.exit(1)
                formats = info.get('formats', [])
                video_resolutions = set()
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        res = f.get('format_note') or f.get('height')
                        if res:
                            if isinstance(res, int):
                                res = f"{res}p"
                            video_resolutions.add(str(res))
                if not video_resolutions:
                    print("❌ No video resolutions found, defaulting to best.")
                    resolution = None
                else:
                    resolution = prompt_resolution(video_resolutions)
        download_video(url, resolution=resolution)
