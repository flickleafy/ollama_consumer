#!/usr/bin/env python3
"""
Test script for Ollama installation and configuration

Copyright (C) 2025 flickleafy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import requests
import json
import os


def test_ollama_api():
    """Test if Ollama API is responding"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def test_model_query(model="llama3"):
    """Test querying a model"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': 'Say hello in exactly 3 words.',
                'stream': False
            },
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json().get('response', '')
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def check_storage_location():
    """Check if models are stored in the correct location"""
    storage_path = "/mnt/[WDG]auxiliary/ollama/.ollama/models"
    if os.path.exists(storage_path):
        files = os.listdir(storage_path)
        return True, f"Storage location exists with {len(files)} items"
    else:
        return False, "Storage location not found"


def main():
    print("=== Ollama Installation Test ===\n")

    # Test 1: API connectivity
    print("1. Testing API connectivity...")
    api_ok, api_result = test_ollama_api()
    if api_ok:
        models = api_result.get('models', [])
        print(f"   ✅ API is working - {len(models)} models available")
        for model in models:
            print(f"      - {model['name']} ({model['size']/1e9:.1f}GB)")
    else:
        print(f"   ❌ API failed: {api_result}")
        return

    # Test 2: Storage location
    print("\n2. Testing storage location...")
    storage_ok, storage_result = check_storage_location()
    if storage_ok:
        print(f"   ✅ {storage_result}")
    else:
        print(f"   ❌ {storage_result}")

    # Test 3: Model query
    print("\n3. Testing model query...")
    if models:
        model_name = models[0]['name']
        query_ok, query_result = test_model_query(model_name)
        if query_ok:
            print(f"   ✅ Model query successful")
            print(f"   Response: {query_result.strip()}")
        else:
            print(f"   ❌ Model query failed: {query_result}")
    else:
        print("   ⏭️  Skipped - no models available")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
