from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.views import HOME_REEL_CODES


class Command(BaseCommand):
    help = "Download home-page Instagram reels into MEDIA_ROOT/reels for clean HTML5 playback."

    def handle(self, *args, **options):
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:
            raise SystemExit(
                "yt-dlp is required. Install with: pip install yt-dlp"
            ) from exc

        out_dir = Path(settings.MEDIA_ROOT) / "reels"
        out_dir.mkdir(parents=True, exist_ok=True)

        urls = [f"https://www.instagram.com/reel/{code}/" for code in HOME_REEL_CODES]
        opts = {
            "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
            ],
            "noplaylist": True,
            "quiet": False,
        }
        with YoutubeDL(opts) as ydl:
            ydl.download(urls)

        self.stdout.write(self.style.SUCCESS(f"Cached {len(urls)} reels in {out_dir}"))
