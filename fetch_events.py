"""Pull upcoming events into events.json from our Luma profiles and withclaude.in. Stdlib only."""
import json, re, sys, urllib.request
from datetime import datetime, timezone

HOSTS = {
    "usr-k46xGae1PxCu2an": "Aniket Sahu",   # luma.com/user/aniketsahu115
    "usr-jY4KvCPqGqRfktq": "Vishal Kumar",  # luma.com/user/Vishal_4743
}
SITES = ["https://www.withclaude.in/events/", "https://www.withclaude.in/"]
UA = {"User-Agent": "Mozilla/5.0 (origin-guild-events)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode()


def text_of(node):
    """Flatten Luma's ProseMirror description doc to plain text."""
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        inner = "".join(text_of(c) for c in node.get("content", []))
        return inner + ("\n" if node.get("type") in ("paragraph", "heading") else "")
    return ""


def event_from_page(slug):
    """Full record from the event page's embedded data; None if private or already over."""
    html = get("https://luma.com/" + slug)
    m = re.search(r'__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not m:
        return None
    data = json.loads(m.group(1))["props"]["pageProps"]["initialData"]["data"]
    ev = data["event"]
    if ev.get("visibility") != "public" or ev["end_at"] < datetime.now(timezone.utc).isoformat():
        return None
    geo = ev.get("geo_address_info") or {}
    where = ", ".join(x for x in (geo.get("sublocality"), geo.get("city"), geo.get("region")) if x) or "Online"
    desc = " ".join(text_of(data.get("description_mirror")).split())
    if len(desc) > 320:
        desc = desc[:317].rsplit(" ", 1)[0] + "…"
    hosts = ", ".join(h["name"] for h in data.get("hosts", []))
    cal = (data.get("calendar") or {}).get("name")
    if cal:
        hosts += " · " + cal
    return {
        "id": ev["url"], "evt": ev["api_id"], "title": ev["name"],
        "start": ev["start_at"], "end": ev["end_at"],
        "where": where, "hosts": hosts, "desc": desc,
        "cover": ev.get("cover_url", ""), "url": "https://luma.com/" + ev["url"],
        "approval": bool((data.get("ticket_info") or {}).get("require_approval")),
    }


def slugs():
    out = []
    for uid in HOSTS:
        d = json.loads(get(f"https://api.lu.ma/user/profile/events-hosting?user_api_id={uid}&period=future&pagination_limit=50"))
        out += [e["event"]["url"] for e in d.get("entries", [])]
    for site in SITES:
        try:
            out += re.findall(r'https?://(?:www\.)?lu(?:ma\.com|\.ma)/([A-Za-z0-9_-]+)', get(site))
        except Exception as e:
            print(f"skip {site}: {e}", file=sys.stderr)
    return [s for s in dict.fromkeys(out) if s not in ("user", "calendar", "embed", "event")]


def main():
    events = []
    for slug in slugs():
        try:
            rec = event_from_page(slug)
        except Exception as e:  # one bad page must not sink the whole run
            print(f"skip {slug}: {e}", file=sys.stderr)
            continue
        if rec:
            events.append(rec)
    events.sort(key=lambda e: e["start"])
    if not events:
        sys.exit("no events fetched; keeping existing events.json")
    json.dump(events, open("events.json", "w"), indent=2, ensure_ascii=False)
    print(f"wrote {len(events)} events")


if __name__ == "__main__":
    main()
