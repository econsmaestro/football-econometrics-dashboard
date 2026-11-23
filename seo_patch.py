import json
import pathlib
import re

import streamlit


def patch_streamlit_shell():
    project_dir = pathlib.Path(__file__).resolve().parent
    static_dir = pathlib.Path(streamlit.__file__).resolve().parent / "static"
    template_path = project_dir / "seo_assets" / "streamlit_shell.html"
    manifest_path = static_dir / "manifest.json"

    template = template_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest.get("index.html")
    if not entry or not entry.get("file") or not entry.get("css"):
        raise RuntimeError("Could not find Streamlit's main JavaScript and CSS bundles.")

    js_bundle = entry["file"]
    css_bundle = entry["css"][0]
    if not (static_dir / js_bundle).is_file() or not (static_dir / css_bundle).is_file():
        raise RuntimeError("Streamlit's main frontend bundle is missing from its static files.")

    template, js_replacements = re.subn(
        r'(<script\b[^>]*\bsrc=["\'])[^"\']+(["\'])',
        rf"\g<1>./{js_bundle}\g<2>",
        template,
        count=1,
    )
    template, css_replacements = re.subn(
        r'(<link\b[^>]*\brel=["\']stylesheet["\'][^>]*\bhref=["\'])[^"\']+(["\'])',
        rf"\g<1>./{css_bundle}\g<2>",
        template,
        count=1,
    )
    if js_replacements != 1 or css_replacements != 1:
        raise RuntimeError("Could not update the Streamlit shell's frontend bundle paths.")

    destination = static_dir / "index.html"
    if not destination.exists() or destination.read_text(encoding="utf-8") != template:
        destination.write_text(template, encoding="utf-8")
    return destination


if __name__ == "__main__":
    print(f"SEO shell applied: {patch_streamlit_shell()}")
