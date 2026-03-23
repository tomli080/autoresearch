import os
import sys
import subprocess
import venv
import tempfile

# Configuration for Strix Halo (gfx1151)
REQUIRED_PYTHON = (3, 12)
VENV_DIR = ".venv"
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")

# Specialized ROCm / TheRock Wheels
ROC_URLS = [
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/rocm-0.1.dev0.tar.gz",
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/rocm_sdk_core-7.13.0a20260313-py3-none-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/rocm_sdk_devel-7.13.0a20260313-py3-none-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/rocm_sdk_libraries_gfx1151-7.13.0a20260313-py3-none-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/torch-2.12.0a0+rocm7.13.0a20260313-cp312-cp312-win_amd64.whl",
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.13.0/torchvision-0.26.0a0+rocm7.13.0a20260313-cp312-cp312-win_amd64.whl"
]

DEPENDENCIES = ["matplotlib", "pandas", "pyarrow", "requests", "rustbpe", "tiktoken"]

def run_cmd(cmd):
    subprocess.check_call(cmd, shell=True)

def verify_env():
    print("--- Hardware Verification ---")
    if not os.path.exists(PYTHON_EXE):
        print("FAIL: Virtual environment not found.")
        return False
    
    # Write a temporary script to avoid quoting hell in shells
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
        # Check if VRAM is roughly 80GB+ (prevents 16GB bug)
        if "VRAM_GB: " in output:
            vram_line = [l for l in output.splitlines() if "VRAM_GB:" in l][0]
            vram_val = float(vram_line.split(":")[1].strip())
            if vram_val < 40: # Strix Halo should be much higher than the 16GB bug cap
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

    print("Building/Repairing environment...")
    run_cmd(f"{PYTHON_EXE} -m pip install --upgrade pip")
    run_cmd(f"{PYTHON_EXE} -m pip install --no-cache-dir {' '.join(ROC_URLS)}")
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
