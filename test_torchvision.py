print("Importing torchvision...")
try:
    import torchvision
    print(f"Torchvision version: {torchvision.__version__}")
except Exception as e:
    print(f"Torchvision failed: {e}")
