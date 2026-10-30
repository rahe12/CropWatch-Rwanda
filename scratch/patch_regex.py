with open('src/advise.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
i = 0
while i < len(lines):
    if 'def extract_district(text):' in lines[i]:
        new_lines.extend([
            'def extract_district(text):\n',
            '    """Senior-grade NER entity extraction: detects any of Rwanda\'s 30 districts from natural text."""\n',
            '    if not text:\n',
            '        return None\n',
            '    raw = text.lower()\n',
            '    for d in RWANDA_DISTRICTS:\n',
            '        pattern = r"\\b" + re.escape(d.lower()) + r"\\b"\n',
            '        if re.search(pattern, raw):\n',
            '            return d\n',
            '    return None\n',
            '\n',
            '\n',
            'def extract_all_districts(text):\n',
            '    """Extracts all mentioned districts for multi-district comparisons."""\n',
            '    if not text:\n',
            '        return []\n',
            '    raw = text.lower()\n',
            '    found = []\n',
            '    for d in RWANDA_DISTRICTS:\n',
            '        pattern = r"\\b" + re.escape(d.lower()) + r"\\b"\n',
            '        if re.search(pattern, raw):\n',
            '            found.append(d)\n',
            '    return found\n',
        ])
        # Skip until def get_followups
        while i < len(lines) and 'def get_followups(' not in lines[i]:
            i += 1
    new_lines.append(lines[i])
    i += 1

with open('src/advise.py', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

print("Updated extract_district and extract_all_districts successfully!")
