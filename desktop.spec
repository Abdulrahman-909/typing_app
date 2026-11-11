from PyInstaller.utils.hooks import collect_submodules
import os
brand=os.environ.get('PROJECT_NAME','TypeAtlas')
a=Analysis(['desktop_entry.py'],pathex=['.'],datas=[('templates','templates'),('static','static'),('staticfiles','staticfiles'),('data','data')],hiddenimports=collect_submodules('apps')+collect_submodules('config')+collect_submodules('django')+['webview','waitress'],excludes=['tkinter','PyQt5','PyQt6','PySide6'])
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name=brand,console=True)
coll=COLLECT(exe,a.binaries,a.datas,name=brand)
