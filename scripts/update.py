"""Reads the Employment News 'All Jobs' table and writes en.json.
Usage: python scripts/update.py            (fetch live)
       python scripts/update.py page.html  (parse a saved file, for testing)
If the fetch or parse fails, en.json is left untouched and the script exits 0."""
import sys, re, json, datetime, pathlib
from bs4 import BeautifulSoup

URL = "https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"
OUT = pathlib.Path(__file__).resolve().parent.parent / "en.json"
DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

def get_html():
    if len(sys.argv) > 1:
        return pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    import requests
    r = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0 (job-hub updater)"})
    r.raise_for_status()
    return r.text

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(td.get_text(" ", strip=True).split()) for td in tr.find_all("td")]
        if len(cells) < 4:
            continue
        m = DATE.match(cells[-1])          # last column = LAST DATE (DD/MM/YYYY)
        if not m:
            continue
        d, mo, y = m.groups()
        org, post, method = cells[-4], cells[-3], cells[-2]
        jobs.append([org.title() if org.isupper() else org, post, method, f"{y}-{mo}-{d}"])
    return jobs

def main():
    try:
        jobs = parse(get_html())
    except Exception as e:
        print("Fetch/parse failed, keeping old data:", e)
        return
    if not jobs:
        print("No rows found, keeping old data")
        return
    jobs.sort(key=lambda j: j[3], reverse=True)
    OUT.write_text(json.dumps({"updated": datetime.date.today().strftime("%d %b %Y").lstrip("0"),
                               "jobs": jobs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(jobs)} jobs")

main()
