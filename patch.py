import os

def patch_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Add import
    if "import torch_directml" not in content:
        content = content.replace("import torch", "import torch\nimport torch_directml\ndml = torch_directml.device()")

    # Patch cuda specific calls
    content = content.replace('torch.cuda.get_device_capability()', '(8, 0)')
    content = content.replace('device="cuda"', 'device=dml')
    content = content.replace('device = torch.device("cuda")', 'device = dml')
    content = content.replace('device_type="cuda"', 'device_type="cpu"')
    content = content.replace('torch.cuda.manual_seed', 'torch.manual_seed')
    content = content.replace('torch.cuda.synchronize()', 'pass')
    content = content.replace('torch.cuda.max_memory_allocated()', '0')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

patch_file("prepare.py")
patch_file("train.py")
print("Patching complete.")
