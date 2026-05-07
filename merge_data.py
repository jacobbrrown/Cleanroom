import sys, json

html_file = "cleanroom_hub.html"
json_file = "cleanroom_merged.json"
out_file  = "cleanroom_hub_updated.html"

print("Reading", html_file)
html = open(html_file, encoding="utf-8").read()

print("Reading", json_file)
data = json.load(open(json_file, encoding="utf-8"))

for key, tag in [("runs","SEED_RUNS"),("rates","SEED_RATES"),("notices","SEED_NOTICES"),("recipes","SEED_RECIPES")]:
    start = "/*" + tag + "_START*/"
    end   = "/*" + tag + "_END*/"
    si = html.find(start)
    ei = html.find(end)
    print(f"  {tag}: start={si}, end={ei}, records={len(data[key])}")
    html = html[:si + len(start)] + json.dumps(data[key], ensure_ascii=False) + html[ei:]

open(out_file, "w", encoding="utf-8").write(html)
print("Written:", out_file)
