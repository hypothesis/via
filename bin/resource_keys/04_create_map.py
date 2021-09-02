import json
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

    mapping_json = json.dumps(mapping, separators=(",", ":")).encode("utf-8")
    file_name = "data/resource_key_mapping.json"
    print(f"Writing {len(mapping_json)} bytes to `{file_name}`")

    with open(file_name, "wb") as handle:
        handle.write(mapping_json)
