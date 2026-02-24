"""
Grynk build script — auto-installs PyInstaller if missing, then builds grynk.exe
"""

import subprocess
import sys
import os


def pip_install(pkg):
    print(f"[build] Installing {pkg}...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])


def check_or_install(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
    except ImportError:
        pip_install(pkg)


def main():
    print("=" * 50)
    print("  Grynk Builder — grynk.exe")
    print("=" * 50)

    # Ensure dependencies
    for pkg, imp in [
        ('pyinstaller', 'PyInstaller'),
        ('colorama',    'colorama'),
        ('requests',    'requests'),
        ('beautifulsoup4', 'bs4'),
    ]:
        check_or_install(pkg, imp)

    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name', 'grynk',
        '--add-data', f'grynk_core{os.pathsep}grynk_core',
        '--hidden-import', 'requests',
        '--hidden-import', 'bs4',
        '--hidden-import', 'colorama',
        '--hidden-import', 'openai',
        'grynk.py',
    ]

    print("\n[build] Running PyInstaller...")
    print("  " + ' '.join(cmd))
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe = os.path.join('dist', 'grynk.exe' if sys.platform == 'win32' else 'grynk')
        print()
        print("=" * 50)
        print(f"  [OK] Build successful!")
        print(f"  Executable: {os.path.abspath(exe)}")
        print()
        print("  To install globally, copy to a directory in PATH:")
        if sys.platform == 'win32':
            print(f"    copy {exe} C:\\Windows\\System32\\grynk.exe")
        else:
            print(f"    sudo cp {exe} /usr/local/bin/grynk")
        print("=" * 50)
    else:
        print()
        print("✖ Build failed. Check the output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
