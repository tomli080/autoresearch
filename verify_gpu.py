import torch

def verify():
    print(f"PyTorch Version: {torch.__version__}")
    
    available = torch.cuda.is_available()
    print(f"ROCm/CUDA Available: {available}")
    
    if available:
        device_count = torch.cuda.device_count()
        print(f"Device Count: {device_count}")
        
        for i in range(device_count):
            name = torch.cuda.get_device_name(i)
            print(f"Device {i} Name: {name}")
            
            props = torch.cuda.get_device_properties(i)
            total_vram_gb = props.total_memory / (1024**3)
            print(f"Device {i} Total VRAM: {total_vram_gb:.2f} GB")
            
            # Check for architecture
            if hasattr(props, 'major') and hasattr(props, 'minor'):
                print(f"Device {i} Compute Capability: {props.major}.{props.minor}")

        # Basic functional test
        try:
            x = torch.randn(1, 3, 224, 224).cuda()
            print("Successfully allocated tensor on GPU.")
        except Exception as e:
            print(f"Failed to allocate tensor on GPU: {e}")
    else:
        print("No ROCm-capable device detected.")

if __name__ == "__main__":
    verify()
