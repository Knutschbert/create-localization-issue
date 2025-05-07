import json
import random
from pathlib import Path

json_files = list(Path('.').rglob('*.json'))

for file_path in json_files:
    try:
        with file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            print(f"Skipping {file_path}: not a Dict[str, str]")
            continue

        keys = list(data.keys())
        half_index = len(keys) // 2

        if half_index == 0:
            print(f"Skipping {file_path}: not enough keys to delete from")
            continue

        num_to_delete = min(random.randint(1, 5), half_index)
        keys_to_delete = random.sample(keys[:half_index], num_to_delete)

        for key in keys_to_delete:
            del data[key]

        with file_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Modified {file_path}: deleted {num_to_delete} keys")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
