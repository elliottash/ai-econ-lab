"""Check the built public lab site and optional live routes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import subprocess
import sys
root = Path(__file__).resolve().parents[1] / 'dist'
class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('href', 'src') or not value or not value.startswith('/') or value.startswith('//'):
                continue
            path = unquote(urlsplit(value).path).lstrip('/')
            if path in ('chat', 'chat/'):
                continue
            target = root / path
            assert target.is_file() or (target / 'index.html').is_file(), (self.page, value)
for page in root.rglob('*.html'):
    text = page.read_text()
    if 'kb' not in page.relative_to(root).parts:
        assert '/summer-school/' not in text and 'Zurich Summer School' not in text, page
        assert 'https://ai-econ-lab.org' in text, page
    parser = Links(); parser.page = page; parser.feed(text)
for name in ('slides','notebooks','assignments','summer-school'):
    assert not (root/name).exists(), name
assert '/kb/' not in (root/'sitemap.xml').read_text()
if '--live' in sys.argv:
    for path, expected in [('/',200),('/people/',200),('/research/',200),('/grants/',200),('/sitemap.xml',200),('/kb/',401),('/kb/euler-to-filesync/',401),('/kb/euler-to-filesync/index.html',401),('/slides/00-course-syllabus.pdf',301),('/summer-school/2026/',301)]:
        status = subprocess.check_output(['curl','-sS','--max-time','30','-o','/dev/null','-w','%{http_code}','https://ai-econ-lab.org'+path],text=True)
        assert status == str(expected), (path,status,expected)
        print(path,status)
    html = subprocess.check_output(['curl','-fsS','--max-time','30','https://ai-econ-lab.org/'],text=True)
    assert 'Economics Lab' in html and 'Zurich Summer School' not in html
print('Lab checks passed.')
