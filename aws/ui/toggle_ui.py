#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile

AWS_DIR = os.path.dirname(os.path.dirname(__file__))
TF_DIR = os.path.join(AWS_DIR, "terraform")

state = sys.argv[1] if len(sys.argv) > 1 else None
if state not in {"on", "off"}:
    print("Usage: toggle_ui.py [on|off]")
    sys.exit(1)

# Get distribution ID
cmd = ["terraform", "output", "-raw", "ui_distribution_id"]
result = subprocess.run(cmd, cwd=TF_DIR, capture_output=True, text=True, check=True)
DIST_ID = result.stdout.strip()

# Get config + ETag
get_cmd = ["aws", "cloudfront", "get-distribution-config", "--id", DIST_ID]
result = subprocess.run(get_cmd, capture_output=True, text=True, check=True)
resp = json.loads(result.stdout)
config = resp["DistributionConfig"]
etag = resp["ETag"]

config["Enabled"] = True if state == "on" else False

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(config, f)
    temp_path = f.name

update_cmd = [
    "aws", "cloudfront", "update-distribution",
    "--id", DIST_ID,
    "--if-match", etag,
    "--distribution-config", f"file://{temp_path}"
]
subprocess.run(update_cmd, check=True)

print(f"✅ UI turned {state.upper()}")
