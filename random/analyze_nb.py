import json

with open('model-final/lung-cancer-severity.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    cell_type = cell['cell_type']
    source = cell['source']
    content = "".join(source)
    print(f"--- Cell {i} ({cell_type}) ---")
    lines = content.split('\n')
    if len(lines) > 5:
        print('\n'.join(lines[:5]))
        print('... (truncated)')
    else:
        print(content)
    print()
