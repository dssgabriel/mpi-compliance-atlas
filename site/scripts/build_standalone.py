"""Package the catalogue as one HTML file that also works over file://."""
import base64
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
(DIST / '.nojekyll').touch()
(DIST / 'NOTICE.md').write_bytes((ROOT / 'NOTICE.md').read_bytes())
html = (DIST / 'index.html').read_text()
css = (DIST / 'style.css').read_text()
js = (DIST / 'app.js').read_text()
stylesheet = re.compile(r'<link rel="stylesheet" href="style\.css(?:\?[^"<>]*)?">')
script = re.compile(r'<script src="app\.js(?:\?[^"<>]*)?" defer></script>')
assert len(stylesheet.findall(html)) == 1, 'Expected one stylesheet reference'
assert len(script.findall(html)) == 1, 'Expected one application script reference'
css_version = hashlib.sha256(css.encode()).hexdigest()[:12]
js_version = hashlib.sha256(js.encode()).hexdigest()[:12]
html = stylesheet.sub(lambda _: '<link rel="stylesheet" href="style.css?v=' + css_version + '">', html)
html = script.sub(lambda _: '<script src="app.js?v=' + js_version + '" defer></script>', html)
(DIST / 'index.html').write_text(html)
logo = (ROOT / 'assets/mpi-forum-logo.svg').read_bytes()
(DIST / 'assets').mkdir(exist_ok=True)
(DIST / 'assets/mpi-forum-logo.svg').write_bytes(logo)
logo_uri = 'data:image/svg+xml;base64,' + base64.b64encode(logo).decode('ascii')
html = html.replace('"assets/mpi-forum-logo.svg"', '"' + logo_uri + '"')
data = (DIST / 'apis.json').read_text()
json.loads(data)
fetch = "fetch('apis.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();})"
assert fetch in js, 'Update the standalone loader to match app.js'
js = js.replace(fetch, "Promise.resolve(JSON.parse(document.getElementById('catalogue-data').textContent))")
html = stylesheet.sub(lambda _: '<style>' + css + '</style>', html)
html = script.sub('', html)
html = html.replace('<a href="apis.json" download>', '<a id="download-data" href="#" download="apis.json">')
html = html.replace('</body>', '<script type="application/json" id="catalogue-data">' + data.replace('<', '\\u003c') + '</script><script>' + js + '\nconst catalogueDownload = new Blob([document.getElementById("catalogue-data").textContent], {type:"application/json"}); document.getElementById("download-data").href = URL.createObjectURL(catalogueDownload);\n</script></body>')
(DIST / 'standalone.html').write_text(html)
print('Built standalone.html: inline styles, scripts, catalogue and JSON download; fonts load from Google Fonts.')
