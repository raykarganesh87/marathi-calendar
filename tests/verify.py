"""Accuracy check: festival dates computed by the engine vs. widely published dates."""
import sys, datetime as dt
sys.path.insert(0, __file__.rsplit('tests', 1)[0])
from marathi_calendar import engine as E

REF = {
 2024: {"महाशिवरात्री": (3, 8), "होळी (होलिका": (3, 24), "गुढीपाडवा": (4, 9), "श्रीरामनवमी": (4, 17),
        "रक्षाबंधन": (8, 19), "श्रीगणेश चतुर्थी": (9, 7), "विजयादशमी": (10, 12),         "गोकुळाष्टमी": (8, 26), "लक्ष्मीपूजन": (10, 31), "अक्षय्य": (5, 10)},
 2025: {"महाशिवरात्री": (2, 26), "होळी (होलिका": (3, 13), "गुढीपाडवा": (3, 30), "श्रीरामनवमी": (4, 6),
        "अक्षय्य": (4, 30), "गुरुपौर्णिमा": (7, 10), "रक्षाबंधन": (8, 9), "श्रीगणेश चतुर्थी": (8, 27),
        "विजयादशमी": (10, 2), "दत्त जयंती": (12, 4), "आषाढी": (7, 6)},
 2026: {"महाशिवरात्री": (2, 15), "होळी (होलिका": (3, 3), "गुढीपाडवा": (3, 19), "श्रीरामनवमी": (3, 26),
        "अक्षय्य": (4, 19), "आषाढी": (7, 25), "गुरुपौर्णिमा": (7, 29), "रक्षाबंधन": (8, 28),
        "श्रीगणेश चतुर्थी": (9, 14), "विजयादशमी": (10, 20)},
}
bad = 0
for yr, ref in REF.items():
    y = E.build(yr)
    for key, (m, d) in ref.items():
        got = [r["date"] for r in y.days if any(key in x for x in r["fest"] + r["vrata"])]
        exp = dt.date(yr, m, d)
        ok = exp in got
        if not ok: bad += 1
        print(yr, "OK " if ok else "BAD", key, "expected", exp, "got", [g.isoformat() for g in got])
    if yr == 2026:
        print("adhik 2026:", [(E.MMONTH[a], b.isoformat(), c.isoformat()) for a, b, c in y.adhik], "(expected Jyeshtha 17 May - 15 Jun)")
print("mismatches:", bad)
