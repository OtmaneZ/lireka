"""Extract slicer visual config from DHL pbix."""
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
        for v in s.get("visualContainers", []):
            cfg = json.loads(v.get("config", "{}"))
            vt = cfg.get("singleVisual", {}).get("visualType", "?")
            if vt == "slicer":
                print("=== SLICER ===")
                print(json.dumps(cfg, indent=2)[:4000])
                print("---")
            if vt == "card":
                print("=== CARD sample ===")
                print(json.dumps(cfg, indent=2)[:2500])
                break
        break
