import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\trija\Documents\LungDetection")

import numpy as np, tensorflow as tf
from tensorflow import keras

print("Loading model...")
model = keras.models.load_model(r"model-final\Lung_Cancer_ResNet50_88Acc.keras", compile=False)

# Check model outputs
print("model.outputs:", model.outputs)
print("len:", len(model.outputs))
for i, o in enumerate(model.outputs):
    print(f"  output[{i}]: {o.shape} name={o.name}")

print()
# Check last few layers
print("Last 5 layers:")
for layer in model.layers[-5:]:
    print(f"  {layer.name}: {type(layer).__name__}")
    if hasattr(layer, 'output'):
        try:
            print(f"    output shape: {layer.output.shape}")
        except:
            print(f"    (output shape unavailable)")
