def read(uri):
    print(f"Reading data from cloud storage: {uri}")
    return b"Cloud data content"

def write(uri, data):
    print(f"Writing data to cloud storage: {uri}")

__all__ = ["read", "write"]
