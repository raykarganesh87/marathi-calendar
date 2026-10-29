import argparse, sys
from .places import PLACES


def cli(argv):
    ap = argparse.ArgumentParser(prog="MarathiCalendarMaker", description="Create a Marathi panchang calendar PDF for a year.")
    ap.add_argument("year", type=int)
    ap.add_argument("--city", default="Nashik", help="one of: " + ", ".join(p[0].split(" (")[0] for p in PLACES))
    ap.add_argument("--lat", type=float); ap.add_argument("--lon", type=float); ap.add_argument("--place", help="Marathi place name for custom lat/lon")
    ap.add_argument("--out", help="output PDF path")
    ap.add_argument("--ad-top", type=float, default=28); ap.add_argument("--ad-bottom", type=float, default=28)
    ap.add_argument("--ad-top-other", type=float, default=20); ap.add_argument("--ad-bottom-other", type=float, default=20)
    a = ap.parse_args(argv)
    from . import render
    if a.lat is not None and a.lon is not None:
        place, lat, lon = a.place or "स्थानिक", a.lat, a.lon
    else:
        m = [p for p in PLACES if p[0].lower().startswith(a.city.lower())]
        if not m: ap.error("unknown city; use --lat/--lon")
        place, lat, lon = m[0][1], m[0][2], m[0][3]
    out = a.out or f"Marathi_Panchang_Calendar_{a.year}.pdf"
    render.make_pdf(a.year, lat, lon, place, out, (a.ad_top, a.ad_bottom), (a.ad_top_other, a.ad_bottom_other),
                    progress=lambda p, m="": print(f"\r{int(p):3d}%", end="", flush=True))
    print("\nSaved:", out)


if __name__ == "__main__":
    if len(sys.argv) > 1: cli(sys.argv[1:])
    else:
        from .gui import main; main()
