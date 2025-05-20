# core/token_estimator.py
import os
import csv
import json

class TokenEstimator:
    """
    Generates tokens.csv files from transcript JSONs under a given project (or subproject).
    """

    def __init__(self, target_folder: str):
        """
        target_folder: path to either a project directory (output/MyProject)
                       or a subproject directory (output/MyProject/MySub).
        """
        self.target_folder = target_folder
        self.tokens_dir = os.path.join(self.target_folder, "tokens")
        os.makedirs(self.tokens_dir, exist_ok=True)
        self.csv_path = os.path.join(self.tokens_dir, "tokens.csv")

    def generate_csv(self):
        """
        Scans all .json files under self.target_folder (recursively),
        writes a CSV with columns [relative_path, token_count],
        and appends a ['TOTAL', total_tokens] row at the end.
        """
        rows = []
        total = 0

        for root, _, files in os.walk(self.target_folder):
            for fn in sorted(files):
                if fn.endswith(".json"):
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, self.target_folder)
                    try:
                        with open(full, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            cnt = int(data.get("token_count", 0))
                    except Exception:
                        cnt = 0
                    rows.append([rel, cnt])
                    total += cnt

        # Write CSV
        with open(self.csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["file", "token_count"])
            writer.writerows(rows)
            writer.writerow(["TOTAL", total])

        return self.csv_path, total
