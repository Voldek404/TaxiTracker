import uuid

PROJECT_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

def make_guid(table, pk):
    return uuid.uuid5(PROJECT_NS, f"{table}:{pk}")