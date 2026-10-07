import json

with open('model-final/notebook482bfa0c7a.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])
    ct = c['cell_type']
    print(f'=== Cell {i} ({ct}) ===')
    print(src[:500])
    print()
