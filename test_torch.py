print("Importing torch...")
try:
    import torch
    print(f"Torch version: {torch.__version__}")
except Exception as e:
    print(f"Torch failed: {e}")
