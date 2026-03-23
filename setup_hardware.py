import os
import sys
import subprocess
import venv
import tempfile

# Configuration for Strix Halo (gfx1151)
REQUIRED_PYTHON = (3, 12)
VENV_DIR = ".venv"
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")

# Specialized ROCm / TheRock Nightly Index for Strix Halo
# This index is dynamically updated by AMD and avoids hardcoded 404 links
ROC_INDEX_URL = "https://rocm.nightlies.amd.com/v2/gfx1151/"

DEPENDENCIES = ["matplotlib", "pandas", "pyarrow", "requests", "rustbpe", "tiktoken"]

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    subprocess.check_call(cmd, shell=True)

def verify_env():
    print("--- Hardware Verification ---")
    if not os.path.exists(PYTHON_EXE):
        print("FAIL: Virtual environment not found.")
        return False
    
    verify_script = """
import torch
try:
    v = torch.__version__
    avail = torch.cuda.is_available()
    print(f"TORCH_VERSION: {v}")
    print(f"GPU_AVAILABLE: {avail}")
    if avail:
        props = torch.cuda.get_device_properties(0)
        vram = props.total_memory / (1024**3)
        print(f"VRAM_GB: {vram:.2f}")
except Exception as e:
    print(f"ERROR: {e}")
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(verify_script)
        tmp_path = tmp.name

    try:
        output = subprocess.check_output(f"{PYTHON_EXE} {tmp_path}", shell=True, text=True)
        print(output.strip())
        os.unlink(tmp_path)
        
        if "GPU_AVAILABLE: True" not in output:
            print("FAIL: ROCm/GPU not detected by PyTorch.")
            return False
        
        if "VRAM_GB: " in output:
            vram_line = [l for l in output.splitlines() if "VRAM_GB:" in l][0]
            vram_val = float(vram_line.split(":")[1].strip())
            if vram_val < 40: 
                print(f"FAIL: VRAM reported ({vram_val}GB) is too low. 16GB bug might be active.")
                return False
            
        print("SUCCESS: Hardware and Environment verified.")
        return True
    except Exception as e:
        if os.path.exists(tmp_path): os.unlink(tmp_path)
        print(f"FAIL: Verification crashed: {e}")
        return False

def setup():
    if sys.version_info[:2] != REQUIRED_PYTHON:
        print(f"ERROR: This hardware build requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}")
        sys.exit(1)

    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)

    print("Building/Repairing environment using Strix Halo Nightly Index...")
    run_cmd(f"{PYTHON_EXE} -m pip install --upgrade pip")
    
    # Install the specialized stack using the dynamic index
    # We use --pre to allow the nightly builds
    print(f"Connecting to: {ROC_INDEX_URL}")
    run_cmd(f"{PYTHON_EXE} -m pip install --pre torch torchvision torchaudio --index-url {ROC_INDEX_URL} --no-cache-dir")
    
    # Install standard dependencies
    print("Installing project dependencies...")
    run_cmd(f"{PYTHON_EXE} -m pip install {' '.join(DEPENDENCIES)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        if verify_env():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        setup()
        verify_env()
