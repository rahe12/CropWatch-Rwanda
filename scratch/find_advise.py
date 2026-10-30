with open('app.py', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'page ==' in line and 'advise' in line:
            print(f'{i+1}: {line.strip()}')
