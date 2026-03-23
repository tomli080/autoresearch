import os
import sys
import subprocess
import venv

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
    
    try:
        # Check torch and GPU
        cmd = f'{PYTHON_EXE} -c "import torch; print(f\'Torch: {torch.__version__}\'); print(f\'GPU: {torch.cuda.is_available()}\'); props=torch.cuda.get_device_properties(0); print(f\'VRAM: {props.total_memory/(1024**3):.2f}GB\')"'
        output = subprocess.check_output(cmd, shell=True, text=True)
        print(output.strip())
        
        if "False" in output:
            print("FAIL: ROCm/GPU not detected by PyTorch.")
            return False
        if "8" not in output: # Check if VRAM is roughly 80GB+ (prevents 16GB bug)
            print("FAIL: VRAM reported is too low. 16GB bug might be active.")
            return False
            
        print("SUCCESS: Hardware and Environment verified.")
        return True
    except Exception as e:
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
