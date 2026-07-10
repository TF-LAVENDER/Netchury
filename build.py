
import platform
from PyInstaller.__main__ import run

opts = [
    'LavenderMain.py',
    '--onefile',
    '--noconsole',
    '--name', 'Netchury',
    '--add-data', 'MainWindow.ui:.',
    '--add-data', 'images:images',
    '--add-data', 'components:components',
]

if platform.system() == 'Darwin':
    # Keep the existing macOS bundle icon and build behavior.
    opts.extend(['-i', 'icon.icns'])
elif platform.system() == 'Windows':
    # Windows Firewall changes require an elevated process. PyInstaller adds the
    # standard UAC manifest so the packaged app requests it once at startup.
    opts.append('--uac-admin')

run(opts)
