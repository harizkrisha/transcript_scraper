# core/dashboard.py
import os
import json

def get_project_level_stats(output_root: str):
    """
    For each project under output_root, compute:
      - total number of transcript JSON files
      - sum of all token_count fields
      - total size in bytes of all JSON files
    Returns a list of [project, total_files, total_tokens, total_bytes].
    """
    stats = []
    for project in sorted(os.listdir(output_root)):
        proj_path = os.path.join(output_root, project)
        if not os.path.isdir(proj_path):
            continue

        total_files = 0
        total_tokens = 0
        total_bytes = 0

        # Walk through subdirectories
        for root, _, files in os.walk(proj_path):
            for fn in files:
                if fn.endswith(".json"):
                    total_files += 1
                    full = os.path.join(root, fn)
                    total_bytes += os.path.getsize(full)
                    try:
                        with open(full, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            total_tokens += int(data.get("token_count", 0))
                    except Exception:
                        # skip malformed JSON
                        pass

        stats.append([project, total_files, total_tokens, total_bytes])
    return stats


def get_subproject_level_stats(output_root: str):
    """
    For each subproject under each project, compute the same metrics:
      - project name, subproject name, total_files, total_tokens, total_bytes
    Returns a list of [project, subproject, total_files, total_tokens, total_bytes].
    """
    stats = []
    for project in sorted(os.listdir(output_root)):
        proj_path = os.path.join(output_root, project)
        if not os.path.isdir(proj_path):
            continue

        # Each immediate subfolder is a subproject
        for sub in sorted(os.listdir(proj_path)):
            sub_path = os.path.join(proj_path, sub)
            if not os.path.isdir(sub_path):
                continue

            total_files = 0
            total_tokens = 0
            total_bytes = 0

            for root, _, files in os.walk(sub_path):
                for fn in files:
                    if fn.endswith(".json"):
                        total_files += 1
                        full = os.path.join(root, fn)
                        total_bytes += os.path.getsize(full)
                        try:
                            with open(full, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                total_tokens += int(data.get("token_count", 0))
                        except Exception:
                            pass

            stats.append([project, sub, total_files, total_tokens, total_bytes])
    return stats
