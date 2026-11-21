# Build from the project root: python -m PyInstaller --distpath build/windows --workpath build/temp packaging/AlemAITrainer.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT=Path(SPECPATH).resolve().parent
datas=[(str(ROOT/'assets'),'assets'),(str(ROOT/'audio'),'audio')]
binaries=[]
hiddenimports=[]
for package in ('panda3d','direct'):
    package_data,package_binaries,package_imports=collect_all(package)
    datas+=package_data
    binaries+=package_binaries
    hiddenimports+=package_imports
a=Analysis([str(ROOT/'main.py')],pathex=[str(ROOT)],binaries=binaries,datas=datas,hiddenimports=hiddenimports,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False,optimize=0)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='AlemAITrainer',debug=False,bootloader_ignore_signals=False,strip=False,upx=True,console=False,disable_windowed_traceback=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=True,name='AlemAITrainer')
