import json, os

with open("generate_type_notebook.py", "r", encoding="utf-8") as f:
    content = f.read()

# We want to keep everything up to the end of Two Phase Training:
target = 'print("\\nTraining selesai! Bobot terbaik sudah dimuat.")"""))'
idx1 = content.find(target)
if idx1 != -1:
    idx1 += len(target)

    # We want to remove everything between idx1 and the start of Cell 10
    target2 = '    # ── 10. Training History Visualization ──────────────────────────────────'
    idx2 = content.find(target2, idx1)

    if idx2 != -1:
        new_content = content[:idx1] + "\n\n" + content[idx2:]
        with open("generate_type_notebook.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully removed old training loop.")
    else:
        print("Could not find start of Cell 10.")
else:
    print("Could not find end of Phase 2.")
