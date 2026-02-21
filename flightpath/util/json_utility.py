
class JsonUtility:

    @classmethod
    def is_jsonl(self, path) -> bool:
        return path.endswith(".jsonl") or path.endswith(".jsonlines") or path.endswith("ndjson")


