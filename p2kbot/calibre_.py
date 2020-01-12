# Adapated from ${PKGDIR}/usr/bin/ebook-convert
import sys
import os

path = os.environ.get("CALIBRE_PYTHON_PATH", "/usr/lib/calibre")
if path not in sys.path:
    sys.path.insert(0, path)

sys.resources_location = os.environ.get("CALIBRE_RESOURCES_PATH", "/usr/share/calibre")
sys.extensions_location = os.environ.get(
    "CALIBRE_EXTENSIONS_PATH", "/usr/lib/calibre/calibre/plugins"
)
sys.executables_location = os.environ.get(
    "CALIBRE_EXECUTABLES_PATH", "/usr/lib/calibre/bin"
)  # FIX

try:
    calibre = __import__("calibre")
except ModuleNotFoundError:
    raise ModuleNotFoundError("Specify CALIBRE_PYTHON_PATH to locate calibre")
