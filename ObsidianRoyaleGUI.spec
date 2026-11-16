from pathlib import Path

project = Path(SPECPATH)
analysis = Analysis(
    [str(project / "app" / "gui_app.py")],
    pathex=[str(project / "app")],
    binaries=[], datas=[], hiddenimports=[], hookspath=[], runtime_hooks=[],
    excludes=["textual", "rich", "pytest"], noarchive=False,
)
# Qt on Windows uses the system ICU API. Do not bundle an unrelated ICU
# found on PATH (for example from Poppler), which can shadow the Windows DLL.
analysis.binaries = [
    entry for entry in analysis.binaries
    if not (Path(entry[0]).name.lower() == "icuuc.dll"
            or Path(entry[0]).name.lower().startswith("icudt"))
]
archive = PYZ(analysis.pure)
exe = EXE(
    archive, analysis.scripts, analysis.binaries, analysis.datas, [],
    name="ObsidianRoyaleGUI", debug=False, strip=False, upx=False, console=False,
)
