"""Run from the isolated Manim environment; publish only original explanatory media."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / 'docs/media'

def run(args):
    subprocess.run(args, cwd=ROOT, check=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('story', choices=['unknown-space', 'footprint-radius'], nargs='?', default='unknown-space')
    story = parser.parse_args().story
    source, scene, check = ('unknown_space', 'UnknownIsNotFree', 'evidence_story') if story == 'unknown-space' else ('footprint_radius', 'FootprintChangesPassage', 'footprint_story')
    video = ROOT / f'artifacts/manim/videos/{source}/720p30/{scene}.mp4'
    if not shutil.which('ffmpeg'):
        raise SystemExit('FFmpeg is required on PATH for the README GIF.')
    run([sys.executable, str(ROOT/f'animations/{check}.py')])
    run([sys.executable, '-m', 'manim', 'render', '--renderer=cairo', '-qm',
         '--media_dir', 'artifacts/manim', f'animations/{source}.py', scene])
    MEDIA.mkdir(exist_ok=True)
    shutil.copy2(video, MEDIA/f'{story}.mp4')
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video),
         '-filter_complex', 'fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
         '-loop', '0', str(MEDIA/f'{story}.gif')])
