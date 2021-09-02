from collections import Counter
from shelve import DbfilenameShelf

with DbfilenameShelf("data/db/file_id.db", flag="r") as db:
    processed = Counter()
    has_resource_key = Counter()
    status_codes = Counter()
    security_status = Counter()
    seen_before = set()
    with_resource_key = []

    for file_id, row in db.items():
        if not row:
            processed[False] += 1
            continue

        processed[True] += 1

        status_code = row["status_code"]
        status_codes[status_code] += 1

        if status_code != 200:
            continue

        has_resource_key[bool(row["resource_key"])] += 1
        if row["resource_key"]:
            with_resource_key.append(file_id)

        if share := row["data"].get("linkShareMetadata"):
            if share["securityUpdateEligible"]:
                if share["securityUpdateEnabled"]:
                    security_status["eligible_and_applied"] += 1
                else:
                    security_status["eligible"] += 1
            else:
                security_status["not_eligible"] += 1
        else:
            security_status[None] += 1

    print("Total", len(db))
    print("Processed:", dict(processed))
    print("Has resource key:", dict(has_resource_key))
    print("Status:", dict(status_codes))
    print("Sec status:", dict(security_status))

    print(with_resource_key)
