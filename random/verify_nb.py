import json, py_compile

with open('model-final/notebook482bfa0c7a-refactored.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

code = '\n'.join([''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code'])

with open('test_type.py', 'w', encoding='utf-8') as f:
    f.write(code)

try:
    py_compile.compile('test_type.py', doraise=True)
    print(f"SYNTAX OK! ({len(nb['cells'])} cells)")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
