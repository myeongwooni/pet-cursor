# PyInstaller spec for Pet Cursor
#
# Build modes:
#   onedir  (default) — folder distribution. Faster startup, recommended.
#   onefile           — single .exe. Convenient to share, but ~10s+ launch time
#                       because the bundle is extracted to %TEMP% every run.
#
# Build:  pyinstaller pet_cursor.spec
# Output: dist/PetCursor/ (onedir)  or  dist/PetCursor.exe (onefile)

# ruff: noqa
# type: ignore

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

ONEFILE = os.environ.get("PET_CURSOR_ONEFILE") == "1"

hiddenimports = []
hiddenimports += collect_submodules("onnxruntime")
hiddenimports += collect_submodules("rembg")
hiddenimports += ["pymatting", "pymatting_aot", "scipy", "scipy.special"]

datas = []
datas += collect_data_files("rembg")
datas += collect_data_files("onnxruntime")
# Some packages call importlib.metadata.version(...) at import time — bundle their dist-info.
for _pkg in ("pymatting", "rembg", "onnxruntime", "numba", "llvmlite", "scipy", "numpy", "Pillow"):
    try:
        datas += copy_metadata(_pkg)
    except Exception:
        pass

excludes = [
    "tkinter",
    "matplotlib",
    "pandas",
    "IPython",
    "notebook",
    "jupyter",
    "pytest",
    "torch",        # rembg can use torch but onnxruntime path doesn't need it
    "tensorflow",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

splash = Splash(
    "assets/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(240, 215),
    text_size=11,
    text_color="#a0a0aa",
    text_default="initializing...",
    minify_script=True,
    always_on_top=True,
)

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        splash,
        splash.binaries,
        [],
        name="PetCursor",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        splash,
        [],
        exclude_binaries=True,
        name="PetCursor",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        splash.binaries,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="PetCursor",
    )

