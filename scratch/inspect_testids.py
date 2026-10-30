import streamlit, os, re
st_path = os.path.dirname(streamlit.__file__)
static_path = os.path.join(st_path, 'static')
for root, dirs, files in os.walk(static_path):
    for f in files:
        if f.endswith('.js'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as js:
                c = js.read()
                matches = set(re.findall(r'data-testid=([a-zA-Z0-9_\-\"\'`]+)', c))
                for m in matches:
                    cleaned = m.strip('"\'`')
                    if any(k in cleaned.lower() for k in ['col', 'horizon', 'vertic', 'pill', 'button']):
                        print("MATCH:", cleaned)
