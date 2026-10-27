"""Verify the real renderer, fonts, H.264 encoding, and audio muxing in a temp project."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
import render


def main():
    subprocess.run([sys.executable, str(ROOT / "engine/get_fonts.py"), "--check"], check=True)
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise RuntimeError(f"Missing {tool}")
    with tempfile.TemporaryDirectory(prefix="vibe-codex-check-") as tmp:
        project = Path(tmp)
        shutil.copyfile(ROOT / "engine/index.html", project / "index.html")
        (project / "film.js").write_text("""VK.film({
  dur: 1, fps: 6, theme: 'night', meta: {title: 'Codex environment check'},
  draw(fr, t) {
    fr.text('云端环境 · 中文字体检查', 960, 460, {size: 64, color: '#ffffff'});
    fr.sfx(0.1, 'tick', {});
  }
});
""", encoding="utf-8")
        (project / "renders").mkdir()

        def check_fonts(page):
            for family in ("VK Serif", "VK Sans"):
                if not page.evaluate("f => document.fonts.check(`48px '${f}'`, '中文')", family):
                    raise RuntimeError(f"Font did not load: {family}")

        render.with_page(project, check_fonts)
        render.frames(project, project / "renders/raw.mp4")
        render.events(project)
        spec = json.loads((project / "audio/events.json").read_text(encoding="utf-8"))
        if not spec["events"]:
            raise RuntimeError("No audio events exported")
        subprocess.run([sys.executable, str(ROOT / "engine/audio.py"), str(project)], check=True)
        probe = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_type,width,height",
            "-of", "json", str(project / "renders/final.mp4")
        ], text=True)
        streams = json.loads(probe)["streams"]
        if not any(s.get("codec_name") == "h264" and s.get("width") == 1920
                   and s.get("height") == 1080 for s in streams):
            raise RuntimeError(f"Unexpected video streams: {streams}")
        if not any(s.get("codec_name") == "aac" for s in streams):
            raise RuntimeError(f"Missing AAC audio: {streams}")
        print("PASS: Chinese fonts, headless browser, 1920x1080 H.264 video, audio events, AAC muxing.")


if __name__ == "__main__":
    main()
