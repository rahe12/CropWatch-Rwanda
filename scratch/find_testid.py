import streamlit, os, re
st_path = os.path.dirname(streamlit.__file__)
static_path = os.path.join(st_path, 'static')
found = set()
for root, dirs, files in os.walk(static_path):
    for f in files:
        if f.endswith('.js'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as js:
                c = js.read()
                matches = re.findall(r'data-testid=[\'"]([^\'"]+)[\'"]', c)
                for m in matches:
                    if 'col' in m.lower():
                        found.add(m)
print("Found column testids:", found)
