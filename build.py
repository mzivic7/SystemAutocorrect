import os
import shutil
import sys

if sys.platform == "win32":
    os.system('pyinstaller --noconfirm --onedir --noconsole --clean --name "Autocorrect" "autocorrect_win.py"')
    os.remove("Autocorrect.spec")
    shutil.rmtree("build")
    shutil.copytree("dist/", "./", dirs_exist_ok=True)
    shutil.rmtree("dist")
    shutil.copy("config.ini", "Autocorrect/config.ini")
    shutil.copytree("keymaps/", "Autocorrect/", dirs_exist_ok=True)
else:
    print("Building is only for Wildows.")
    sys.exit()
