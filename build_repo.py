import hashlib
import os
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_ZIPS = ROOT / "zips"

ADDONS = [
    ROOT / "repository.profiler",
    ROOT / "script.kodi.profiler",
]

def read_addon_xml(addon_dir: Path) -> str:
    p = addon_dir / "addon.xml"
    if not p.exists():
        raise FileNotFoundError(f"Missing addon.xml in {addon_dir}")
    return p.read_text(encoding="utf-8")

def get_id_and_version(addon_xml: str):
    # Simple parse: id="..." version="..."
    m_id = re.search(r'<addon[^>]+id="([^"]+)"', addon_xml)
    m_ver = re.search(r'<addon[^>]+version="([^"]+)"', addon_xml)
    if not m_id or not m_ver:
        raise ValueError("Could not parse id/version from addon.xml")
    return m_id.group(1), m_ver.group(1)

def zip_addon(addon_dir: Path, addon_id: str, version: str) -> Path:
    # output: zips/<id>/<id>-<version>.zip
    target_dir = OUT_ZIPS / addon_id
    target_dir.mkdir(parents=True, exist_ok=True)

    zip_path = target_dir / f"{addon_id}-{version}.zip"

    # Create zip where top-level folder is the addon folder name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file_path in addon_dir.rglob("*"):
            if file_path.is_dir():
                continue
            rel = file_path.relative_to(addon_dir.parent)  # includes addon folder name
            z.write(file_path, rel.as_posix())

    return zip_path

def make_addons_xml(addon_xml_list: list[str]) -> str:
    # Kodi expects <addons> containing concatenated <addon> nodes
    # Remove xml declaration lines if present
    cleaned = []
    for xml in addon_xml_list:
        xml = re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml)
        cleaned.append(xml.strip())

    out = "<addons>\n" + "\n".join(cleaned) + "\n</addons>\n"
    return out

def md5_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def main():
    # Clean previous output
    if OUT_ZIPS.exists():
        shutil.rmtree(OUT_ZIPS)
    OUT_ZIPS.mkdir(parents=True, exist_ok=True)

    addon_xmls = []

    for addon_dir in ADDONS:
        addon_xml = read_addon_xml(addon_dir)
        addon_id, version = get_id_and_version(addon_xml)
        addon_xmls.append(addon_xml)

        zip_path = zip_addon(addon_dir, addon_id, version)
        print(f"Zipped: {zip_path}")

    addons_xml = make_addons_xml(addon_xmls)
    (ROOT / "addons.xml").write_text(addons_xml, encoding="utf-8")
    (ROOT / "addons.xml.md5").write_text(md5_text(addons_xml), encoding="utf-8")

    print("Wrote: addons.xml")
    print("Wrote: addons.xml.md5")
    print("Done.")

if __name__ == "__main__":
    main()
