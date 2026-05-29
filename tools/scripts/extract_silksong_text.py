import argparse
import csv
import html
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import UnityPy
from UnityPy import config


config.FALLBACK_UNITY_VERSION = "6000.0.0f1"


GROUPS = {
    "Song": ["EN_Song", "ZH_Song", "ZH_TW_Song"],
    "UI": ["EN_UI", "ZH_UI", "ZH_TW_UI"],
    "Achievements": ["EN_Achievements", "ZH_Achievements", "ZH_TW_Achievements"],
    "Credits_List": ["EN_Credits_List", "ZH_Credits_List", "ZH_TW_Credits_List"],
}


def find_data_dir(root: Path) -> Path:
    candidates = [
        root / "Hollow Knight Silksong_Data",
        root,
    ]
    for candidate in candidates:
        if (candidate / "resources.assets").exists() and (candidate / "Managed" / "Assembly-CSharp.dll").exists():
            return candidate
    raise FileNotFoundError(f"Cannot find resources.assets and Managed/Assembly-CSharp.dll under {root}")


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")


def canonical_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def read_text_assets(resources_assets: Path) -> dict[str, str]:
    env = UnityPy.load(str(resources_assets))
    assets = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.read()
        name = getattr(data, "name", None) or getattr(data, "m_Name", "")
        script = getattr(data, "script", None)
        if script is None:
            script = getattr(data, "m_Script", b"")
        if isinstance(script, bytes):
            text = script.decode("utf-8", errors="replace")
        else:
            text = str(script)
        assets[name] = text
    return assets


def load_decrypt_method(assembly_path: Path):
    import clr  # noqa: F401 - initializes pythonnet so the System namespace is available.
    import System
    from System.Reflection import BindingFlags

    assembly = System.Reflection.Assembly.LoadFile(str(assembly_path))
    string_encrypt = assembly.GetType("StringEncrypt")
    if string_encrypt is None:
        raise RuntimeError("StringEncrypt type was not found in Assembly-CSharp.dll")
    method = string_encrypt.GetMethod("DecryptData", BindingFlags.Public | BindingFlags.Static)
    if method is None:
        raise RuntimeError("StringEncrypt.DecryptData was not found in Assembly-CSharp.dll")
    return method


def decrypt_assets(assets: dict[str, str], assembly_path: Path) -> dict[str, str]:
    method = load_decrypt_method(assembly_path)
    decrypted = {}
    for name, text in assets.items():
        try:
            value = method.Invoke(None, [text])
            decrypted[name] = str(value)
        except Exception:
            continue
    return decrypted


def parse_entries(text: str) -> dict[str, str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    entries = {}
    for entry in root.findall(".//entry"):
        key = entry.attrib.get("name")
        if not key:
            continue
        value = "".join(entry.itertext())
        entries[key] = html.unescape(value)
    return entries


def write_group_csv(out_dir: Path, group_name: str, names: list[str], decrypted: dict[str, str]) -> None:
    by_canonical = {canonical_name(key): value for key, value in decrypted.items()}
    parsed = {}
    for name in names:
        text = decrypted.get(name, "") or by_canonical.get(canonical_name(name), "")
        parsed[name] = parse_entries(text)
    keys = sorted(set().union(*(entries.keys() for entries in parsed.values())))
    if not keys:
        return

    csv_path = out_dir / f"{group_name}_EN_ZH.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", *names])
        for key in keys:
            writer.writerow([key, *(parsed[name].get(key, "") for name in names)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and decrypt Hollow Knight: Silksong text assets.")
    parser.add_argument("--root", required=True, help="Game root, depot root, or Hollow Knight Silksong_Data folder.")
    parser.add_argument("--out", required=True, help="Output root directory.")
    parser.add_argument("--label", required=True, help="Version label used as the output folder name.")
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out) / safe_name(args.label)
    data_dir = find_data_dir(root)
    resources_assets = data_dir / "resources.assets"
    assembly_path = data_dir / "Managed" / "Assembly-CSharp.dll"

    encrypted_dir = out_dir / "textassets_encrypted"
    decrypted_dir = out_dir / "textassets_decrypted"
    csv_dir = out_dir / "csv"
    for directory in [encrypted_dir, decrypted_dir, csv_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    assets = read_text_assets(resources_assets)
    for name, text in sorted(assets.items()):
        (encrypted_dir / f"{safe_name(name)}.txt").write_text(text, encoding="utf-8")

    decrypted = decrypt_assets(assets, assembly_path)
    for name, text in sorted(decrypted.items()):
        (decrypted_dir / f"{safe_name(name)}.txt").write_text(text, encoding="utf-8")

    for group_name, names in GROUPS.items():
        write_group_csv(csv_dir, group_name, names, decrypted)

    shutil.copy2(resources_assets, out_dir / "resources.assets")
    shutil.copy2(assembly_path, out_dir / "Assembly-CSharp.dll")
    build_metadata = data_dir / "StreamingAssets" / "BuildMetadata.json"
    if build_metadata.exists():
        shutil.copy2(build_metadata, out_dir / "BuildMetadata.json")
    summary = out_dir / "EXTRACTION_SUMMARY.txt"
    summary.write_text(
        "\n".join(
            [
                f"label={args.label}",
                f"source_root={root}",
                f"data_dir={data_dir}",
                f"resources_assets={resources_assets}",
                f"assembly_path={assembly_path}",
                f"text_assets_found={len(assets)}",
                f"text_assets_decrypted={len(decrypted)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Exported {len(decrypted)} decrypted TextAssets to {out_dir}")


if __name__ == "__main__":
    main()
