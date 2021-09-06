import json
import os
from shelve import DbfilenameShelf


def get_mapping():
    with DbfilenameShelf("data/db/file_id.db", flag="r") as db:
        return {
            file_id: data["data"]["resourceKey"]
            for file_id, data in db.items()
            if data and data["resource_key"]
        }


if __name__ == "__main__":
    mapping = get_mapping()
    print(f"Mapping {len(mapping)} items")

    file_name = "data/resource_key_mapping.json"
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as handle:
            data = json.load(handle)
            print(f"Existing file has {len(data)} rows")

    print(f"New data has {len(mapping)} rows")

    mapping_json = json.dumps(mapping, separators=(",", ":")).encode("utf-8")
    print(f"Writing {len(mapping_json)} bytes to `{file_name}`")

    with open(file_name, "wb") as handle:
        handle.write(mapping_json)
