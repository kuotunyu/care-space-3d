"""Run from the isolated Manim environment; publish only original explanatory media."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / 'artifacts/manim/videos/unknown_space/720p30/UnknownIsNotFree.mp4'
MEDIA = ROOT / 'docs/media'

def run(args):
    subprocess.run(args, cwd=ROOT, check=True)

if __name__ == '__main__':
    if not shutil.which('ffmpeg'):
        raise SystemExit('FFmpeg is required on PATH for the README GIF.')
    run([sys.executable, str(ROOT/'animations/evidence_story.py')])
    run([sys.executable, '-m', 'manim', 'render', '--renderer=cairo', '-qm',
         '--media_dir', 'artifacts/manim', 'animations/unknown_space.py', 'UnknownIsNotFree'])
    MEDIA.mkdir(exist_ok=True)
    shutil.copy2(VIDEO, MEDIA/'unknown-space.mp4')
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(VIDEO),
         '-filter_complex', 'fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
         '-loop', '0', str(MEDIA/'unknown-space.gif')])
