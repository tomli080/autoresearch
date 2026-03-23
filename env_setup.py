import os

# Specialized ROCm / Strix Halo (gfx1151) Configuration
os.environ["PYTORCH_ROCM_ARCH"] = "gfx1151"
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.5.1"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

# Memory and Logging
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

print(f"Hardware environment initialized for gfx1151 (Strix Halo)")
