"""Debug helper — print raw 400 response body for link_test_cases_to_cycle."""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import httpx

API_KEY = os.environ["QMETRY_API_KEY"]
BASE = os.environ.get("QMETRY_BASE_URL", "https://qtmcloud.qmetry.com/rest/api/latest/").rstrip("/") + "/"

headers = {"apiKey": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}

# IDs and keys from last search_test_cases run
TC_KEYS = ["DEV-TC-13", "DEV-TC-12", "DEV-TC-11"]
TC_IDS  = ["V2NDSb53sz3LGZ", "661ZFWjQuYDLzd", "16nwF2OWCLAR3d"]

# Cycles created in last run — try both internal ID and key
CYCLES = [
    ("DEV-TR-7 internal id",  "661ZFWjQuQm1WP"),
    ("DEV-TR-7 key",          "DEV-TR-7"),
    ("DEV-TR-5 internal id",  "DDZQHqw1FxOJAm"),
    ("DEV-TR-5 key",          "DEV-TR-5"),
]

payloads = [
    ("testCaseKeys array",                        {"testCaseKeys": TC_KEYS}),
    ("filter.testCaseKeys",                       {"filter": {"testCaseKeys": TC_KEYS}}),
    ("filter.key",                                {"filter": {"key": TC_KEYS}}),
    ("filter.keys",                               {"filter": {"keys": TC_KEYS}}),
    ("filter.projectId only",                     {"filter": {"projectId": "10000"}}),
    ("filter.projectId + testCaseKeys",           {"filter": {"projectId": "10000", "testCaseKeys": TC_KEYS}}),
    ("filter.projectId int + testCaseKeys",       {"filter": {"projectId": 10000, "testCaseKeys": TC_KEYS}}),
]

# Only iterate over one cycle (DEV-TR-7 key) to keep output manageable
TARGET_CYCLES = [("DEV-TR-7 key", "DEV-TR-7")]

with httpx.Client(base_url=BASE, headers=headers, timeout=30) as client:
    for cycle_label, cycle_ref in TARGET_CYCLES:
        for p_label, body in payloads:
            url = f"testcycles/{cycle_ref}/testcases"
            r = client.post(url, json=body)
            print(f"\n[{r.status_code}] {p_label}")
            print(f"  Body : {json.dumps(body)}")
            try:
                print(f"  Resp : {json.dumps(r.json(), indent=2)}")
            except Exception:
                print(f"  Resp : {r.text!r}")
            if r.is_success:
                print("  *** SUCCESS ***")
