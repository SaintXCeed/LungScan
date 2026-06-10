import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r'c:\Users\trija\Documents\LungDetection\model-final\integrated-lung-cancer-diagnostic-pipeline-ipynb (4).ipynb'
nb = json.load(open(path, encoding='utf-8'))
cells = nb['cells']

# Full source of cell 2 (the main code cell)
c = cells[2]
print(''.join(c['source']))
