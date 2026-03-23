import os
import sys
import subprocess
import venv
import tempfile

# 1. Path Management: Ensure we find the .venv regardless of where the script is called from
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")

if os.name == "nt":
    PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe")
else:
    PYTHON_EXE = os.path.join(VENV_DIR, "bin", "python")

# Configuration for Strix Halo (gfx1151)
REQUIRED_PYTHON = (3, 12)

# Specialized ROCm / TheRock Nightly Index for Strix Halo
# This index is dynamically updated by AMD and avoids hardcoded 404 links
ROC_INDEX_URL = "https://rocm.nightlies.amd.com/v2/gfx1151/"

DEPENDENCIES = ["matplotlib", "pandas", "pyarrow", "requests", "rustbpe", "tiktoken"]

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    # Use shell=True for Windows compatibility, but capture output for better debugging
    subprocess.check_call(cmd, shell=True)

def verify_env():
    print(f"--- Hardware Verification (using {PYTHON_EXE}) ---")
    if not os.path.exists(PYTHON_EXE):
        print(f"FAIL: Virtual environment not found at {PYTHON_EXE}")
        return False
    
    # Write a temporary script to avoid quoting hell in shells
    verify_script = """
import sys
import os
try:
    import torch
    v = torch.__version__
    avail = torch.cuda.is_available()
    print(f"TORCH_VERSION: {v}")
    print(f"GPU_AVAILABLE: {avail}")
    if avail:
        props = torch.cuda.get_device_properties(0)
        vram = props.total_memory / (1024**3)
        print(f"VRAM_GB: {vram:.2f}")
except ImportError:
    print("FAIL: 'torch' module not found in the virtual environment.")
except Exception as e:
    print(f"ERROR: {e}")
"""
    
    # Create temp file in the current directory to ensure it's cleanup-able
    tmp_path = os.path.join(SCRIPT_DIR, "_verify_tmp.py")
    with open(tmp_path, 'w') as f:
        f.write(verify_script)

    try:
        # Run the python from the venv explicitly
        output = subprocess.check_output(f'"{PYTHON_EXE}" {tmp_path}', shell=True, text=True, stderr=subprocess.STDOUT)
        print(output.strip())
        
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
    except subprocess.CalledProcessError as e:
        print(f"FAIL: Verification execution failed with exit code {e.returncode}")
        print(f"Output: {e.output}")
        return False
    except Exception as e:
        print(f"FAIL: Verification crashed: {e}")
        return False
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)

def setup():
    if sys.version_info[:2] != REQUIRED_PYTHON:
        print(f"ERROR: This hardware build requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}")
        sys.exit(1)

    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment at {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)

    print("Building/Repairing environment using Strix Halo Nightly Index...")
    run_cmd(f'"{PYTHON_EXE}" -m pip install --upgrade pip')
    
    # Install the specialized stack using the dynamic index
    print(f"Connecting to: {ROC_INDEX_URL}")
    run_cmd(f'"{PYTHON_EXE}" -m pip install --pre torch torchvision torchaudio --index-url {ROC_INDEX_URL} --no-cache-dir')
    
    # Install standard dependencies
    print("Installing project dependencies...")
    run_cmd(f'"{PYTHON_EXE}" -m pip install {" ".join(DEPENDENCIES)}')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        if verify_env():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        setup()
        verify_env()
