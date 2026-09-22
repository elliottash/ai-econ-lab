from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
root = Path(__file__).resolve().parents[1] / "dist"
urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
for page in sorted(root.rglob("index.html")):
    rel = page.parent.relative_to(root)
    if rel.parts and rel.parts[0] == "kb":
        continue
    path = "/" if str(rel) == "." else "/" + rel.as_posix() + "/"
    SubElement(SubElement(urlset, "url"), "loc").text = "https://ai-econ-lab.org" + path
ElementTree(urlset).write(root / "sitemap.xml", encoding="utf-8", xml_declaration=True)
