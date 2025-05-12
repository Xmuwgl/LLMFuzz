import struct
import random
import secrets
from pathlib import Path
import yaml

def parse_config(config_path: str) -> dict:
    """Parsing"""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Check
    if "memory_map" not in config or "mmio" not in config["memory_map"]:
        raise ValueError("Lack `memory_map.mmio` in setting file")
    
    mmio_config = config["memory_map"]["mmio"]
    if "base_addr" not in mmio_config:
        raise ValueError("Lack `base_addr` in setting file")
    
    base_addr = mmio_config["base_addr"]
    if not isinstance(base_addr, (int, str)):
        raise TypeError(f"[TYPE ERROR]: base_addr. Dec or hex string needed, current type: {type(base_addr)}")
    
    # Convert
    if isinstance(base_addr, str):
        if not base_addr.startswith("0x"):
            raise ValueError(f"[FORMAT ERROR]: base_addr. Beginning should be `0x`: {base_addr}")
        base_addr = int(base_addr, 16)
    
    return {"mmio_base_addr": base_addr}


def generate_random_data(min_len: int = 1, max_len: int = 1000) -> bytes:
    data_length = random.randint(min_len, max_len)
    return secrets.token_bytes(data_length) 


def generate_seed_bin(
    output_path: str,
    mmio_base_addr: int,
    initial_data: bytes
):

    header = b'mul\x01'

    num_streams = 1
    num_streams_bytes = struct.pack('<I', num_streams)
    
    if not isinstance(mmio_base_addr, int) or mmio_base_addr < 0:
        raise ValueError(f"mmio_base_addr should be non-negative, current value = {mmio_base_addr}")
    address_bytes = struct.pack('<Q', mmio_base_addr)
    
    data_length = len(initial_data)
    if not (1 <= data_length <= 1000):
        raise ValueError(f"data length limit: 1-1000 Byte, current length: {data_length}")
    data_length_bytes = struct.pack('<Q', data_length)
    
    bin_data = header + num_streams_bytes + address_bytes + data_length_bytes + initial_data
    Path(output_path).write_bytes(bin_data)
    print(f"Generate successfully! {output_path}")


def main():
    config_path = input("Specify config.yml\n")
    
    try:
        config = parse_config(config_path)
        mmio_base_addr = config["mmio_base_addr"]
        
        initial_data = generate_random_data()
        
        for i in range(0, 1001):
            output_path = f'workdir/queue/{i}.bin'
            generate_seed_bin(output_path, mmio_base_addr, initial_data)
    
    except Exception as e:
        print(f"生成失败: {str(e)}")
        exit(1)
