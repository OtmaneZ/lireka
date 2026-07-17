"""Extract DHL Vue 360 layout from pbix for reference."""
import json
import zipfile
from pathlib import Path

pbix = Path(
    r"C:\Users\Otmane\Documents\lireka\Power_BI_Datawarehouse"
    r"\Dashboards_transporteurs\DHL Dashboard PowerBI\02_Power BI"
    r"\DHL_dashboard_PowerBi_Version_Finale (2).pbix"
)
with zipfile.ZipFile(pbix) as z:
    layout = z.read("Report/Layout").decode("utf-16-le")
data = json.loads(layout)
for s in data.get("sections", []):
    if "360" in s.get("displayName", ""):
        print("page:", s.get("displayName"))
        for v in s.get("visualContainers", []):
            cfg = json.loads(v.get("config", "{}"))
            vt = cfg.get("singleVisual", {}).get("visualType", "?")
            pos = (v.get("x"), v.get("y"), v.get("width"), v.get("height"))
            print(f"  {vt:22} {pos}")
        break
