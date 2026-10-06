"""Pull upcoming events hosted by our Luma profiles into events.json. Stdlib only."""
import json, re, sys, urllib.request

HOSTS = {
    "usr-k46xGae1PxCu2an": "Aniket Sahu",   # luma.com/user/aniketsahu115
    "usr-jY4KvCPqGqRfktq": "Vishal Kumar",  # luma.com/user/Vishal_4743
}
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


def event_details(slug):
    html = get("https://luma.com/" + slug)
    data = json.loads(re.search(r'__NEXT_DATA__" type="application/json">(.*?)</script>', html).group(1))
    data = data["props"]["pageProps"]["initialData"]["data"]
    desc = " ".join(text_of(data.get("description_mirror")).split())
    if len(desc) > 320:
        desc = desc[:317].rsplit(" ", 1)[0] + "…"
    hosts = ", ".join(h["name"] for h in data.get("hosts", []))
    cal = (data.get("calendar") or {}).get("name")
    if cal:
        hosts += " · " + cal
    return desc, hosts, bool((data.get("ticket_info") or {}).get("require_approval"))


def main():
    seen = {}
    for uid in HOSTS:
        d = json.loads(get(f"https://api.lu.ma/user/profile/events-hosting?user_api_id={uid}&period=future&pagination_limit=50"))
        for entry in d.get("entries", []):
            ev = entry["event"]
            if ev.get("visibility") != "public" or ev["api_id"] in seen:
                continue
            geo = ev.get("geo_address_info") or {}
            where = ", ".join(x for x in (geo.get("sublocality"), geo.get("city"), geo.get("region")) if x) or "Online"
            desc, hosts, approval = event_details(ev["url"])
            seen[ev["api_id"]] = {
                "id": ev["url"], "evt": ev["api_id"], "title": ev["name"],
                "start": ev["start_at"], "end": ev["end_at"],
                "where": where, "hosts": hosts, "desc": desc,
                "cover": ev.get("cover_url", ""), "url": "https://luma.com/" + ev["url"],
                "approval": approval,
            }
    events = sorted(seen.values(), key=lambda e: e["start"])
    if not events:
        sys.exit("no events fetched; keeping existing events.json")
    json.dump(events, open("events.json", "w"), indent=2, ensure_ascii=False)
    print(f"wrote {len(events)} events")


if __name__ == "__main__":
    main()
