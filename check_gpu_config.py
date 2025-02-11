#!/usr/bin/env python3
"""
Check GPU configuration for Ollama optimization
"""

import subprocess
import json
import os


def check_nvidia_gpus():
    """Check NVIDIA GPU configuration"""
    try:
        # Get GPU information
        cmd = [
            'nvidia-smi',
            '--query-gpu=index,name,memory.total,memory.free,memory.used,utilization.gpu,power.draw,temperature.gpu',
            '--format=csv,noheader,nounits'
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)

        gpus = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = [p.strip() for p in line.split(',')]
                gpu_info = {
                    'index': int(parts[0]),
                    'name': parts[1],
                    'memory_total_mb': int(parts[2]),
                    'memory_free_mb': int(parts[3]),
                    'memory_used_mb': int(parts[4]),
                    'utilization_percent': int(parts[5]) if parts[5] != '[Not Supported]' else 0,
                    'power_draw_w': float(parts[6]) if parts[6] != '[Not Supported]' else 0,
                    'temperature_c': int(parts[7]) if parts[7] != '[Not Supported]' else 0
                }
                gpus.append(gpu_info)

        return gpus

    except subprocess.CalledProcessError as e:
        print(f"Error running nvidia-smi: {e}")
        return []
    except Exception as e:
        print(f"Error parsing GPU info: {e}")
        return []


def check_ollama_env():
    """Check current Ollama environment variables"""
    ollama_vars = {}

    env_vars = [
        'CUDA_VISIBLE_DEVICES',
        'OLLAMA_GPU_MEMORY_FRACTION',
        'OLLAMA_MAX_LOADED_MODELS',
        'OLLAMA_GPU_LAYERS',
        'OLLAMA_HOST',
        'OLLAMA_PORT'
    ]

    for var in env_vars:
        value = os.environ.get(var)
        if value:
            ollama_vars[var] = value

    return ollama_vars


def recommend_gpu_config(gpus):
    """Recommend optimal GPU configuration"""
    if not gpus:
        return "No NVIDIA GPUs found!"

    # Sort GPUs by memory capacity (primary indicator of capability)
    sorted_gpus = sorted(
        gpus, key=lambda x: x['memory_total_mb'], reverse=True)

    print("\n🎯 GPU Configuration Recommendations:")
    print("=" * 50)

    primary_gpu = sorted_gpus[0]
    print(
        f"🥇 Primary GPU (Index {primary_gpu['index']}): {primary_gpu['name']}")
    print(
        f"   Memory: {primary_gpu['memory_total_mb']:,} MB total, {primary_gpu['memory_free_mb']:,} MB free")

    if len(sorted_gpus) > 1:
        secondary_gpu = sorted_gpus[1]
        print(
            f"🥈 Secondary GPU (Index {secondary_gpu['index']}): {secondary_gpu['name']}")
        print(
            f"   Memory: {secondary_gpu['memory_total_mb']:,} MB total, {secondary_gpu['memory_free_mb']:,} MB free")

        # Recommend CUDA_VISIBLE_DEVICES order
        primary_idx = primary_gpu['index']
        secondary_idx = secondary_gpu['index']

        print(f"\n📋 Recommended Environment Variables:")
        print(f"export CUDA_VISIBLE_DEVICES={primary_idx},{secondary_idx}")
        print(f"export OLLAMA_GPU_MEMORY_FRACTION=0.9")
        print(f"export OLLAMA_MAX_LOADED_MODELS=1")

        print(f"\n💡 This configuration will:")
        print(
            f"   • Prioritize GPU {primary_idx} ({primary_gpu['name']}) for single-GPU models")
        print(
            f"   • Use GPU {secondary_idx} ({secondary_gpu['name']}) only when model splitting is needed")
        print(f"   • Reserve 10% GPU memory for system operations")
    else:
        print(f"\n📋 Single GPU detected - no multi-GPU configuration needed")
        print(f"export OLLAMA_GPU_MEMORY_FRACTION=0.9")


def main():
    print("🔍 Checking GPU Configuration for Ollama")
    print("=" * 50)

    # Check GPUs
    gpus = check_nvidia_gpus()

    if gpus:
        print(f"Found {len(gpus)} NVIDIA GPU(s):")
        print()

        for gpu in gpus:
            utilization_bar = "█" * \
                (gpu['utilization_percent'] // 10) + "░" * \
                (10 - gpu['utilization_percent'] // 10)
            memory_used_pct = (gpu['memory_used_mb'] /
                               gpu['memory_total_mb']) * 100
            memory_bar = "█" * int(memory_used_pct // 10) + \
                "░" * (10 - int(memory_used_pct // 10))

            print(f"GPU {gpu['index']}: {gpu['name']}")
            print(
                f"  💾 Memory: {gpu['memory_used_mb']:,}/{gpu['memory_total_mb']:,} MB ({memory_used_pct:.1f}%) [{memory_bar}]")
            print(
                f"  ⚡ Utilization: {gpu['utilization_percent']}% [{utilization_bar}]")
            print(f"  🌡️  Temperature: {gpu['temperature_c']}°C")
            print(f"  🔌 Power: {gpu['power_draw_w']:.1f}W")
            print()
    else:
        print("❌ No NVIDIA GPUs found or nvidia-smi not available")
        return

    # Check current environment
    print("🔧 Current Ollama Environment Variables:")
    print("-" * 40)
    ollama_env = check_ollama_env()

    if ollama_env:
        for var, value in ollama_env.items():
            print(f"  {var}={value}")
    else:
        print("  No Ollama environment variables set")

    print()

    # Provide recommendations
    recommend_gpu_config(gpus)


if __name__ == "__main__":
    main()
