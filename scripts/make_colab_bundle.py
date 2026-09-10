"""Small source-only handoff. No user data, assets, weights or environments in ZIP."""
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
(root/"notebooks").mkdir(exist_ok=True)
def cell(kind,source):
    value={"cell_type":kind,"metadata":{},"source":source.splitlines(keepends=True)}
    if kind=="code":value.update(execution_count=None,outputs=[])
    return value
cells=[cell("markdown","""# CareSpace 3D · CPU reproducibility launcher

This notebook installs and invokes the same project core. It contains no separate
geometry/model implementation. It has not been executed in this development session.
The verified adapter uses CPU float32; no particular Colab GPU is assumed.

Place the provided `care-space-3d-source.zip` in `MyDrive/CareSpace3D/`. This is source
code, not a dataset collection task. The scripts acquire the exact legal research
subset (8.67 MB) and one checkpoint (1.34 GB) themselves. ReplicaCAD's pinned LICENSE
is CC BY-NC 4.0 despite the official page's CC BY 4.0 label; local research only.
Assets, models, per-frame predictions and results persist in the Drive work folder.
"""),cell("code","""from google.colab import drive
drive.mount('/content/drive')
from pathlib import Path
from zipfile import ZipFile
import subprocess, sys, shutil
SOURCE = Path('/content/drive/MyDrive/CareSpace3D/care-space-3d-source.zip')
PROJECT = Path('/content/drive/MyDrive/CareSpace3D/work-v01')
PROJECT.mkdir(parents=True, exist_ok=True)
with ZipFile(SOURCE) as z:
    for member in z.infolist():
        destination = (PROJECT / member.filename).resolve()
        if not destination.is_relative_to(PROJECT.resolve()):
            raise ValueError('Unexpected archive path')
    z.extractall(PROJECT)
ENV = Path('/content/carespace-venv')
subprocess.run([sys.executable, '-m', 'venv', str(ENV)], check=True)
PYTHON = str(ENV / 'bin/python')
subprocess.run([PYTHON, '-m', 'pip', 'install', '-r', str(PROJECT/'requirements-cpu.lock')], check=True)
subprocess.run([PYTHON, '-m', 'pip', 'install', '--no-deps', '-e', str(PROJECT)], check=True)
"""),cell("code","""# Downloads resume; existing matching predictions are reused.
for script in ['fetch_assets.py', 'fetch_model.py', 'run_study.py', 'run_learning.py', 'build_report.py', 'build_depth_audit.py', 'run_abstention.py']:
    subprocess.run([PYTHON, str(PROJECT/'scripts'/script)], cwd=PROJECT, check=True)
print((PROJECT/'docs/results.md').read_text())
"""),cell("code","""# Optional notebook-local viewer; uses the same static frontend.
if shutil.which('npm'):
    subprocess.run(['npm', 'ci'], cwd=PROJECT, check=True)
    subprocess.run(['node', str(PROJECT/'scripts/build_diagnostics.mjs')], cwd=PROJECT, check=True)
    server = subprocess.Popen([PYTHON, '-m', 'http.server', '8840', '--bind', '127.0.0.1'], cwd=PROJECT)
    from google.colab import output
    output.serve_kernel_port_as_iframe(8840, path='/viewer/', height=800)
else:
    print('Node/npm unavailable; analysis artifacts are saved. Use the local viewer commands in README.md.')
""")]
notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5}
(root/"notebooks/colab.ipynb").write_text(json.dumps(notebook,indent=2),encoding="utf8")
target=root/"artifacts/care-space-3d-source.zip"
with ZipFile(target,"w",ZIP_DEFLATED) as z:
    for folder in ["src","scripts","configs","viewer","docs","notebooks"]:
        for p in (root/folder).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:z.write(p,p.relative_to(root).as_posix())
    for filename in ["pyproject.toml","requirements-cpu.lock","package.json","package-lock.json","README.md"]:
        p=root/filename
        if p.exists():z.write(p,filename)
print(f"Wrote {target} ({target.stat().st_size} bytes)")
