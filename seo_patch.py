import streamlit, pathlib, shutil

src = pathlib.Path(__file__).parent / "seo_assets" / "streamlit_shell.html"
dst = pathlib.Path(streamlit.__file__).parent / "static" / "index.html"
shutil.copy(src, dst)
print(f"SEO shell applied: {dst}")
