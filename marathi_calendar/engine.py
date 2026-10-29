"""
Marathi panchang engine.

Computes, for any Gregorian year and any place in India (IST):
tithi / nakshatra / yoga / karana / moon-sign with end times, sunrise & sunset,
amanta lunar months (incl. adhik masa), Shaka / Vikram / Samvatsara, sankrantis,
eclipses, Hijri dates and festival / vrata dates (rule based).

Astronomy: Swiss Ephemeris (Moshier mode, no data files needed), Lahiri ayanamsa.
"""
import datetime as dt
import swisseph as swe
from dateutil.easter import easter

swe.set_sid_mode(swe.SIDM_LAHIRI)
FL = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
FLT = swe.FLG_MOSEPH
IST = 5.5 / 24.0
SYNODIC = 29.530588853

# ---------------------------------------------------------------- names
_DEV = str.maketrans("0123456789", "०१२३४५६७८९")
def dn(x): return str(x).translate(_DEV)

WEEK_S = ["सोम", "मंगळ", "बुध", "गुरु", "शुक्र", "शनि", "रवि"]
WEEK = ["सोमवार", "मंगळवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
GREG = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै", "ऑगस्ट",
        "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
MMONTH = ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक",
          "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"]
TITHI = ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
         "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी"]
NAK = ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशीर्ष", "आर्द्रा", "पुनर्वसू", "पुष्य", "आश्लेषा",
       "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा",
       "ज्येष्ठा", "मूळ", "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शततारका",
       "पूर्वा भाद्रपदा", "उत्तरा भाद्रपदा", "रेवती"]
YOGA = ["विष्कुंभ", "प्रीती", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगंड", "सुकर्मा", "धृती", "शूल",
        "गंड", "वृद्धी", "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धी", "व्यतीपात", "वरीयान",
        "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "ऐंद्र", "वैधृती"]
RASHI = ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुळ", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
KARANA_MOVING = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टी (भद्रा)"]
KARANA_FIXED = {58: "शकुनी", 59: "चतुष्पाद", 60: "नाग", 1: "किंस्तुघ्न"}
HIJRI_M = ["मोहरम", "सफर", "रबिउल अव्वल", "रबिउल आखर", "जमादिउल अव्वल", "जमादिउल आखर",
           "रजब", "शाबान", "रमजान", "शव्वाल", "जिल्कद", "जिल्हेज"]
SAMVATSARA = ["प्रभव", "विभव", "शुक्ल", "प्रमोद", "प्रजापती", "अंगिरा", "श्रीमुख", "भाव", "युवा", "धाता",
              "ईश्वर", "बहुधान्य", "प्रमाथी", "विक्रम", "वृष", "चित्रभानू", "स्वभानू", "तारण", "पार्थिव",
              "व्यय", "सर्वजित", "सर्वधारी", "विरोधी", "विकृत", "खर", "नंदन", "विजय", "जय", "मन्मथ",
              "दुर्मुख", "हेमलंबी", "विलंबी", "विकारी", "शार्वरी", "प्लव", "शुभकृत", "शोभकृत", "क्रोधी",
              "विश्वावसू", "पराभव", "प्लवंग", "कीलक", "सौम्य", "साधारण", "विरोधकृत", "परिधावी", "प्रमादी",
              "आनंद", "राक्षस", "नल", "पिंगल", "कालयुक्त", "सिद्धार्थी", "रौद्र", "दुर्मती", "दुंदुभी",
              "रुधिरोद्गारी", "रक्ताक्षी", "क्रोधन", "अक्षय"]

EK_NAMES = {  # amanta (month idx, paksha 0=shuddha 1=vadya)
    (0, 0): "कामदा", (0, 1): "वरुथिनी", (1, 0): "मोहिनी", (1, 1): "अपरा",
    (2, 0): "निर्जला", (2, 1): "योगिनी", (3, 0): "आषाढी (देवशयनी)", (3, 1): "कामिका",
    (4, 0): "पुत्रदा (श्रावण)", (4, 1): "अजा", (5, 0): "परिवर्तिनी (पद्मा)", (5, 1): "इंदिरा",
    (6, 0): "पापांकुशा", (6, 1): "रमा", (7, 0): "कार्तिकी (प्रबोधिनी)", (7, 1): "उत्पत्ती",
    (8, 0): "मोक्षदा", (8, 1): "सफला", (9, 0): "पुत्रदा (पौष)", (9, 1): "षटतिला",
    (10, 0): "जया (भैमी)", (10, 1): "विजया", (11, 0): "आमलकी", (11, 1): "पापमोचनी"}


def tithi_name(n):
    if n == 15: return "पौर्णिमा"
    if n == 30: return "अमावास्या"
    return TITHI[(n - 1) % 15]


def tithi_full(n, month=None, adhik=False):
    k = (n - 1) % 15 + 1
    pk = "शुद्ध" if n <= 15 else "वद्य"
    pre = (("अधिक " if adhik else "") + MMONTH[month] + " ") if month is not None else ""
    if n in (15, 30): return pre + tithi_name(n)
    return f"{pre}{pk} {TITHI[k - 1]}"


# ---------------------------------------------------------------- low level astronomy
def jd_of(d, h=0.0):
    """JD(UT) for IST local date d at IST hour h."""
    return swe.julday(d.year, d.month, d.day, 0.0) + (h / 24.0) - IST

def to_ist(jd):
    y, m, d, h = swe.revjul(jd + IST)
    mins = int(round(h * 60))
    return dt.datetime(y, m, d) + dt.timedelta(minutes=mins)

def _sid(jd, body): return swe.calc_ut(jd, body, FL)[0][0]
def _trop(jd, body): return swe.calc_ut(jd, body, FLT)[0][0]
def elong(jd): return (_sid(jd, swe.MOON) - _sid(jd, swe.SUN)) % 360
def moon_l(jd): return _sid(jd, swe.MOON)
def sun_l(jd): return _sid(jd, swe.SUN)
def yoga_ang(jd): return (_sid(jd, swe.MOON) + _sid(jd, swe.SUN)) % 360
def tithi_at(jd): return int(elong(jd) // 12) + 1

def next_cross(fn, jd, period, span=2.0):
    """First time after jd at which fn (an increasing angle, deg) reaches a multiple of period."""
    target = (int(fn(jd) // period) + 1) * period
    def delta(t): return ((fn(t) - target + 180) % 360) - 180
    lo, hi = jd, jd + span
    for _ in range(36):
        mid = (lo + hi) / 2
        if delta(mid) < 0: lo = mid
        else: hi = mid
    return (lo + hi) / 2

def karana_at(jd):
    n = int(elong(jd) // 6) + 1
    if n == 1 or n >= 58: return KARANA_FIXED[n]
    return KARANA_MOVING[(n - 2) % 7]

def find_new_moons(jd_start, jd_end):
    out, t = [], jd_start
    while t < jd_end:
        a = t
        while True:
            b = a + 0.5
            if elong(b) < elong(a) - 180:
                lo, hi = a, b; break
            a = b
        for _ in range(40):
            mid = (lo + hi) / 2
            if elong(mid) > 180: lo = mid
            else: hi = mid
        nm = (lo + hi) / 2
        out.append(nm)
        t = nm + 20
    return out


# ---------------------------------------------------------------- the calendar object
class Year:
    pass


def build(year, lat=19.9975, lon=73.7898, place="नाशिक", progress=None):
    """Compute everything for `year`. Returns a Year object."""
    def tick(p, msg=""):
        if progress: progress(p, msg)

    geo = (lon, lat, 0.0)
    D0 = dt.date(year, 1, 1)
    ndays = (dt.date(year + 1, 1, 1) - D0).days

    def rise_set(d, body, rs):
        res, t = swe.rise_trans(jd_of(d, 0), body, rs, geo, 1013.25, 15.0, FLT)
        return t[0]
    sunrise = lambda d: rise_set(d, swe.SUN, swe.CALC_RISE)
    sunset = lambda d: rise_set(d, swe.SUN, swe.CALC_SET)

    def moonrise_after(jd):
        res, t = swe.rise_trans(jd, swe.MOON, swe.CALC_RISE, geo, 1013.25, 15.0, FLT)
        return t[0]

    # ---- new moons & lunar months
    tick(2, "अमावास्या गणना")
    new_moons = find_new_moons(jd_of(dt.date(year - 1, 11, 20)), jd_of(dt.date(year + 1, 3, 15)))
    nm_info = []
    for i in range(len(new_moons) - 1):
        rs = int(sun_l(new_moons[i]) // 30); re_ = int(sun_l(new_moons[i + 1]) // 30)
        nm_info.append(((rs + 1) % 12, rs == re_))   # (month idx, adhik)

    def lunar_month(jd):
        # binary search
        lo, hi = 0, len(new_moons) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if new_moons[mid] <= jd: lo = mid
            else: hi = mid
        return nm_info[lo][0], nm_info[lo][1], new_moons[lo]

    # ---- Hijri (moon-visibility estimate), anchored on Ramadan 1448 = lunation starting 6 Feb 2027
    anchor = find_new_moons(jd_of(dt.date(2027, 2, 3)), jd_of(dt.date(2027, 2, 12)))[0]
    h_starts = []
    for nm in new_moons:
        d0 = to_ist(nm).date()
        for k in range(0, 3):
            d = d0 + dt.timedelta(days=k)
            ss = sunset(d)
            if ss <= nm: continue
            el = abs(((_trop(ss, swe.MOON) - _trop(ss, swe.SUN) + 180) % 360) - 180)
            if (ss - nm) * 24 >= 19 and el >= 9.5:
                lun = round((nm - anchor) / SYNODIC)
                h_starts.append((d + dt.timedelta(days=1), (8 + lun) % 12, 1448 + (8 + lun) // 12))
                break

    def hijri_of(d):
        cur = None
        for s, m, y in h_starts:
            if s <= d: cur = (s, m, y)
        s, m, y = cur
        return (d - s).days + 1, m, y

    # ---- daily base records
    DAYS = []
    for i in range(ndays):
        d = D0 + dt.timedelta(days=i)
        sr = sunrise(d); ss = sunset(d); nsr = sunrise(d + dt.timedelta(days=1))
        t = sr + 1 / 1440
        mi, adhik, _ = lunar_month(t)
        DAYS.append(dict(
            date=d, wd=d.weekday(), sr=sr, ss=ss, nsr=nsr, month=mi, adhik=adhik,
            tithi=tithi_at(t), tithi_end=next_cross(elong, t, 12),
            nak=int(moon_l(t) // (360 / 27)), nak_end=next_cross(moon_l, t, 360 / 27),
            yoga=int(yoga_ang(t) // (360 / 27)), yoga_end=next_cross(yoga_ang, t, 360 / 27),
            karana=karana_at(t), karana_end=next_cross(elong, t, 6),
            rashi=int(moon_l(t) // 30), rashi_end=next_cross(moon_l, t, 30),
            hijri=hijri_of(d), fest=[], vrata=[], holiday=False))
        if i % 15 == 0: tick(5 + 40 * i / ndays, "दैनंदिन पंचांग")

    def find_day(d): return DAYS[(d - D0).days]

    # ---- Gudi Padwa / Shaka
    gudi = None
    for r in DAYS:
        if r["month"] == 0 and not r["adhik"] and r["tithi"] <= 2 and r["date"].month >= 3:
            gudi = r["date"]; break
    if gudi is None: gudi = dt.date(year, 4, 1)

    def shaka_of(d): return year - 78 if d >= gudi else year - 79

    # ---- helpers for festival rules
    def kind_time(kind, r):
        sr, ss, nsr = r["sr"], r["ss"], r["nsr"]; L = ss - sr
        return {"sunrise": sr + 1 / 1440, "aruna": sr - 60 / 1440, "madhyahna": sr + L / 2,
                "aparahna": sr + 0.7 * L, "pradosh": ss + 45 / 1440, "nishita": ss + (nsr - ss) / 2}[kind]

    _kc = {}
    def kt(i, kind):
        key = (i, kind)
        if key not in _kc:
            t = kind_time(kind, DAYS[i])
            m, ad, _ = lunar_month(t)
            _kc[key] = (m, ad, tithi_at(t))
        return _kc[key]

    def add(d, text, hol=False, vrata=False):
        if not (D0 <= d < dt.date(year + 1, 1, 1)): return
        r = find_day(d)
        if text not in r["fest"] and text not in r["vrata"]:
            (r["vrata"] if vrata else r["fest"]).append(text)
        if hol: r["holiday"] = True

    def tithi_dates(month, tithi, kinds):
        for kind in kinds:
            found = [DAYS[i]["date"] for i in range(ndays)
                     if kt(i, kind)[0] == month and not kt(i, kind)[1] and kt(i, kind)[2] == tithi]
            if found: return found
        before = tithi - 1 if tithi > 1 else 30
        after = tithi + 1 if tithi < 30 else 1
        out = []
        for i, r in enumerate(DAYS):
            t, t2 = r["sr"] + 1 / 1440, r["nsr"] + 1 / 1440
            m, ad, _ = lunar_month(t2)
            if m == month and not ad and tithi_at(t) == before and tithi_at(t2) == after:
                out.append(r["date"])
        return out

    # ---------------------------------------------------------------- festival table
    FEST = [
        (0, 0, 1, ["sunrise"], "गुढीपाडवा – हिंदू नववर्ष प्रारंभ", True),
        (0, 0, 9, ["madhyahna", "sunrise"], "श्रीरामनवमी", True),
        (0, 0, 13, ["sunrise", "madhyahna"], "महावीर जयंती", True),
        (0, 0, 15, ["sunrise", "madhyahna"], "हनुमान जयंती / चैत्र पौर्णिमा", False),
        (1, 0, 3, ["madhyahna", "sunrise"], "अक्षय्य तृतीया", False),
        (1, 0, 14, ["pradosh"], "नृसिंह जयंती", False),
        (1, 0, 15, ["sunrise", "madhyahna"], "बुद्ध पौर्णिमा", True),
        (2, 0, 15, ["aparahna", "sunrise"], "वटपौर्णिमा", False),
        (3, 0, 15, ["sunrise", "madhyahna"], "गुरुपौर्णिमा (व्यास पौर्णिमा)", False),
        (3, 1, 15, ["sunrise", "madhyahna"], "दीप अमावास्या (गटारी)", False),
        (4, 0, 5, ["madhyahna", "sunrise"], "नागपंचमी", False),
        (4, 0, 15, ["aparahna", "sunrise"], "नारळी पौर्णिमा / रक्षाबंधन", False),
        (4, 1, 8, ["nishita", "sunrise"], "गोकुळाष्टमी (श्रीकृष्ण जयंती)", False),
        (4, 1, 15, ["sunrise", "madhyahna"], "पिठोरी अमावास्या – बैलपोळा", False),
        (5, 0, 3, ["sunrise", "madhyahna"], "हरतालिका", False),
        (5, 0, 4, ["madhyahna", "sunrise"], "श्रीगणेश चतुर्थी", True),
        (5, 0, 5, ["madhyahna", "sunrise"], "ऋषिपंचमी", False),
        (5, 0, 14, ["sunrise", "madhyahna"], "अनंत चतुर्दशी (गणेश विसर्जन)", True),
        (5, 1, 1, ["sunrise", "madhyahna"], "महालय पक्ष (पितृपंधरवडा) प्रारंभ", False),
        (5, 1, 15, ["sunrise", "madhyahna"], "सर्वपित्री अमावास्या", False),
        (6, 0, 1, ["sunrise"], "घटस्थापना – शारदीय नवरात्रारंभ", False),
        (6, 0, 5, ["sunrise"], "ललिता पंचमी", False),
        (6, 0, 8, ["madhyahna", "sunrise"], "दुर्गाष्टमी (महाष्टमी)", False),
        (6, 0, 9, ["madhyahna", "sunrise"], "महानवमी (खंडेनवमी)", False),
        (6, 0, 10, ["aparahna", "sunrise"], "विजयादशमी (दसरा)", True),
        (6, 0, 15, ["nishita", "sunrise"], "कोजागरी पौर्णिमा", False),
        (6, 1, 12, ["pradosh", "sunrise"], "वसुबारस (गोवत्स द्वादशी)", False),
        (6, 1, 13, ["pradosh", "sunrise"], "धनत्रयोदशी (धन्वंतरी जयंती)", False),
        (6, 1, 14, ["aruna", "sunrise"], "नरकचतुर्दशी (अभ्यंगस्नान)", False),
        (6, 1, 15, ["pradosh", "sunrise"], "लक्ष्मीपूजन (दिवाळी अमावास्या)", True),
        (7, 0, 1, ["sunrise"], "बलिप्रतिपदा (दिवाळी पाडवा)", True),
        (7, 0, 2, ["aparahna", "sunrise"], "भाऊबीज", False),
        (7, 0, 12, ["sunrise", "pradosh"], "तुलसी विवाहारंभ", False),
        (7, 0, 15, ["sunrise", "madhyahna"], "त्रिपुरारी पौर्णिमा / गुरुनानक जयंती", True),
        (7, 1, 13, ["madhyahna", "sunrise"], "संत ज्ञानेश्वर महाराज समाधी दिन", False),
        (8, 0, 6, ["madhyahna", "sunrise"], "चंपाषष्ठी (खंडोबा नवरात्र समाप्ती)", False),
        (8, 0, 11, ["sunrise"], "गीता जयंती", False),
        (8, 0, 15, ["pradosh", "sunrise"], "दत्त जयंती", False),
        (9, 0, 15, ["sunrise", "madhyahna"], "शाकंभरी पौर्णिमा", False),
        (10, 0, 4, ["madhyahna", "sunrise"], "माघी गणेश जयंती", False),
        (10, 0, 5, ["sunrise", "madhyahna"], "वसंतपंचमी (सरस्वती पूजन)", False),
        (10, 0, 7, ["sunrise"], "रथसप्तमी", False),
        (10, 0, 15, ["sunrise", "madhyahna"], "माघी पौर्णिमा", False),
        (10, 1, 9, ["madhyahna", "sunrise"], "दासनवमी (समर्थ रामदास स्वामी पुण्यतिथी)", False),
        (10, 1, 14, ["nishita"], "महाशिवरात्री", True),
        (11, 0, 15, ["pradosh"], "होळी (होलिका दहन)", False),
        (11, 1, 1, ["sunrise"], "धुलिवंदन", True),
        (11, 1, 2, ["sunrise"], "संत तुकाराम बीज", False),
        (11, 1, 3, ["sunrise", "madhyahna"], "छत्रपती शिवाजी महाराज जयंती (तिथीनुसार)", False),
        (11, 1, 5, ["sunrise"], "रंगपंचमी", False),
        (11, 1, 6, ["madhyahna", "sunrise"], "एकनाथ षष्ठी", False),
    ]
    for idx, (m, pk, k, kinds, label, hol) in enumerate(FEST):
        n = k + (15 if pk else 0)
        if k == 15 and pk == 1: n = 30
        dates = tithi_dates(m, n, kinds)
        note = ""
        vishti = lambda tt: karana_at(tt).startswith("विष्टी")
        if label.startswith("होळी") and dates:
            d0 = dates[0]; tp = kind_time("pradosh", find_day(d0))
            if vishti(tp):
                bend = next_cross(elong, tp, 6)
                if bend <= jd_of(d0 + dt.timedelta(days=1), 0):
                    note = " (भद्रा समाप्तीनंतर)"
                else:
                    d0 = d0 + dt.timedelta(days=1); note = " (भद्रा काळ टाळून)"
            dates = [d0]
        if label.startswith("नारळी"):
            cand = [dd for dd in tithi_dates(m, n, ["aparahna"])
                    if not vishti(kind_time("aparahna", find_day(dd)))]
            if not cand: cand = tithi_dates(m, n, ["sunrise"]) or tithi_dates(m, n, ["madhyahna"])
            dates = cand
        if dates:
            r0 = find_day(dates[0]); i0 = (dates[0] - D0).days
            lab = label + note
            if all(kt(i0, kd)[2] != n for kd in kinds) and not note:
                lab += " (तिथी क्षय – वेळ पाहावी)"
            if m == 0 and k == 1 and pk == 0:
                lab = f"गुढीपाडवा – हिंदू नववर्ष शके {dn(shaka_of(dates[0]))} प्रारंभ ({SAMVATSARA[(shaka_of(dates[0]) + 11) % 60]} संवत्सर)"
            add(dates[0], lab, hol)
        if idx % 6 == 0: tick(48 + 20 * idx / len(FEST), "सण-उत्सव")

    # month beginnings
    for i in range(1, ndays):
        r, pv = DAYS[i], DAYS[i - 1]
        if (r["month"], r["adhik"]) != (pv["month"], pv["adhik"]):
            add(r["date"], ("अधिक " if r["adhik"] else "") + MMONTH[r["month"]] + " मास प्रारंभ")

    # Shravan days
    for r in DAYS:
        if r["month"] == 4 and not r["adhik"]:
            if r["wd"] == 0: add(r["date"], "श्रावणी सोमवार")
            if r["wd"] == 1: add(r["date"], "मंगळागौरी पूजन")

    # ---- vratas
    for i, r in enumerate(DAYS):
        n = r["tithi"]; pk = 0 if n <= 15 else 1
        prev_same = i > 0 and DAYS[i - 1]["tithi"] == n
        next_same = i + 1 < ndays and DAYS[i + 1]["tithi"] == n
        if n in (11, 26):
            nm = EK_NAMES.get((r["month"], pk), "")
            if r["adhik"]: nm = "अधिक मास – " + ("पद्मिनी" if pk == 0 else "परम")
            suffix = " (भागवत)" if prev_same else (" (स्मार्त)" if next_same else "")
            add(r["date"], f"{nm} एकादशी{suffix}", vrata=True)
        tm = kind_time("madhyahna", r)
        for tt, lab in ((15, "पौर्णिमा"), (30, "अमावास्या")):
            if n == tt or tithi_at(tm) == tt:
                add(r["date"], lab, vrata=True)

    VIN = set()
    for r in DAYS:
        mr = moonrise_after(r["ss"] - 1.0 / 24)
        if to_ist(mr).date() == r["date"] and tithi_at(mr) == 19:
            nm = "अंगारकी संकष्टी चतुर्थी" if r["wd"] == 1 else "संकष्ट चतुर्थी"
            add(r["date"], f"{nm} (चंद्रोदय {dn(to_ist(mr).strftime('%H:%M'))})", vrata=True)
            r["sankashti"] = True
        t = kind_time("madhyahna", r)
        if tithi_at(t) == 4 and (r["date"] - dt.timedelta(days=1)) not in VIN:
            VIN.add(r["date"]); add(r["date"], "विनायकी चतुर्थी", vrata=True)
        t = kind_time("pradosh", r)
        if tithi_at(t) in (13, 28):
            add(r["date"], f"{WEEK_S[r['wd']]} प्रदोष", vrata=True)
        t = kind_time("nishita", r)
        if tithi_at(t) == 29 and not any("महाशिवरात्री" in x for x in r["fest"]):
            add(r["date"], "मासिक शिवरात्री", vrata=True)
    for i in range(ndays - 1):
        if DAYS[i].get("sankashti") and DAYS[i + 1].get("sankashti"):
            DAYS[i]["vrata"] = [x for x in DAYS[i]["vrata"] if "संकष्ट" not in x]
            DAYS[i]["sankashti"] = False
    have, done = set(), set()
    for r in DAYS:
        if r.get("sankashti"): have.add(lunar_month(r["sr"])[2])
    for r in DAYS:
        s0 = lunar_month(r["sr"])[2]
        if s0 in have or s0 in done: continue
        if tithi_at(kind_time("pradosh", r)) == 19:
            done.add(s0)
            add(r["date"], "अंगारकी संकष्टी चतुर्थी" if r["wd"] == 1 else
                "संकष्ट चतुर्थी (चंद्रोदयाला तिथी नाही – प्रदोषकाळ; चंद्रोदय पाहावा)", vrata=True)
    tick(72, "संक्रांती")

    # ---- sankrantis
    SANK = []
    t = jd_of(dt.date(year, 1, 1)) - 35
    for _ in range(16):
        t2 = next_cross(sun_l, t, 30, span=40)
        ist = to_ist(t2)
        if ist.year == year:
            SANK.append((ist, int(sun_l(t2 + 0.01) // 30)))
        t = t2 + 5
    for ist, ri in SANK:
        d = ist.date()
        if ri == 9:
            add(d, f"मकर संक्रांत (सूर्य मकर राशीत – {dn(ist.strftime('%H:%M'))})")
            if jd_of(d, ist.hour + ist.minute / 60) > find_day(d)["ss"]:
                add(d + dt.timedelta(days=1), "मकर संक्रांत (पुण्यकाल)")
        else:
            add(d, f"{RASHI[ri]} संक्रांत ({dn(ist.strftime('%H:%M'))})")

    # ---- fixed (Gregorian) observances
    FIXED = {
        (1, 1): ("नववर्षारंभ", False), (1, 3): ("सावित्रीबाई फुले जयंती", False),
        (1, 12): ("राजमाता जिजाऊ जयंती / स्वामी विवेकानंद जयंती", False),
        (1, 23): ("नेताजी सुभाषचंद्र बोस जयंती", False), (1, 26): ("प्रजासत्ताक दिन", True),
        (1, 30): ("हुतात्मा दिन (महात्मा गांधी पुण्यतिथी)", False),
        (2, 19): ("छत्रपती शिवाजी महाराज जयंती (तारखेनुसार)", True),
        (2, 28): ("राष्ट्रीय विज्ञान दिन", False), (3, 8): ("जागतिक महिला दिन", False),
        (3, 10): ("सावित्रीबाई फुले स्मृतिदिन", False),
        (4, 14): ("डॉ. बाबासाहेब आंबेडकर जयंती", True), (5, 1): ("महाराष्ट्र दिन / कामगार दिन", True),
        (6, 6): ("शिवराज्याभिषेक दिन", False), (7, 1): ("कृषी दिन", False),
        (8, 1): ("लोकमान्य टिळक पुण्यतिथी / अण्णाभाऊ साठे जयंती", False),
        (8, 15): ("स्वातंत्र्य दिन", True), (9, 5): ("शिक्षक दिन", False),
        (9, 17): ("मराठवाडा मुक्तिसंग्राम दिन", False),
        (10, 2): ("महात्मा गांधी जयंती", True), (11, 14): ("बालदिन", False),
        (12, 6): ("महापरिनिर्वाण दिन (डॉ. आंबेडकर)", False), (12, 25): ("नाताळ (ख्रिसमस)", True),
    }
    for (m, dd), (txt, hol) in FIXED.items():
        add(dt.date(year, m, dd), txt, hol)
    es = easter(year)
    add(es - dt.timedelta(days=2), "गुड फ्रायडे", True)
    add(es, "ईस्टर संडे")

    # ---- Hijri festivals (moon-sighting dependent => '*')
    HFEST = {(1, 10): "मोहरम (आशुरा)", (9, 1): "रमजान मास प्रारंभ", (9, 27): "शब-ए-कद्र",
             (10, 1): "रमजान ईद (ईद-उल-फित्र)", (12, 10): "बकरी ईद (ईद-उल-अज़हा)",
             (8, 15): "शब-ए-बरात", (3, 12): "ईद-ए-मिलाद (पैगंबर जयंती)"}
    for r in DAYS:
        hd, hm, hy = r["hijri"]
        key = (hm + 1, hd)
        if key in HFEST:
            add(r["date"], HFEST[key] + " *", hol=key in [(1, 10), (10, 1), (12, 10), (3, 12)])
    tick(80, "ग्रहणे")

    # ---- eclipses
    ECL = []
    end_jd = jd_of(dt.date(year + 1, 1, 1))
    t = jd_of(D0)
    while True:
        ret, tret = swe.sol_eclipse_when_glob(t, FLT, 0, False)
        if tret[0] > end_jd: break
        vis = False
        try:
            rl, tl, attr = swe.sol_eclipse_when_loc(tret[0] - 1, geo, FLT, False)
            vis = bool(rl & 128) and abs(tl[0] - tret[0]) < 1
        except Exception:
            pass
        ECL.append(("सूर्यग्रहण", to_ist(tret[0]), ret, vis))
        t = tret[0] + 20
    t = jd_of(D0)
    while True:
        ret, tret = swe.lun_eclipse_when(t, FLT, 0, False)
        if tret[0] > end_jd: break
        vis = False
        try:
            rl, tl, attr = swe.lun_eclipse_when_loc(tret[0] - 1, geo, FLT, False)
            vis = bool(rl & 128) and not (ret & 64)
        except Exception:
            pass
        ECL.append(("चंद्रग्रहण", to_ist(tret[0]), ret, vis))
        t = tret[0] + 20
    ECL = sorted([e for e in ECL if e[1].year == year], key=lambda x: x[1])
    def ecl_label(e):
        if e[0] == "चंद्रग्रहण":
            if e[2] & 64: return "छायाकल्प चंद्रग्रहण"
            return ("खग्रास " if e[2] & 4 else "खंडग्रास ") + "चंद्रग्रहण"
        return ("कंकणाकृती " if e[2] & 8 else ("खग्रास " if e[2] & 4 else "खंडग्रास ")) + "सूर्यग्रहण"
    for e in ECL:
        lab = ecl_label(e)
        if e[0] == "चंद्रग्रहण" and e[2] & 64:
            lab += " (उपछाया – धार्मिक नियम लागू नाहीत)"
        else:
            lab += f" ({place} येथून दिसेल)" if e[3] else f" ({place} येथून दिसणार नाही)"
        add(e[1].date(), lab)

    y = Year()
    y.year, y.place, y.lat, y.lon = year, place, lat, lon
    y.days, y.sank, y.ecl, y.ecl_label = DAYS, SANK, ECL, ecl_label
    y.gudi, y.shaka_of = gudi, shaka_of
    y.samvatsara_of = lambda d: SAMVATSARA[(shaka_of(d) + 11) % 60]
    adh = []
    for r in DAYS:
        if r["adhik"] and (not adh or adh[-1][0] != r["month"]): adh.append([r["month"], r["date"], r["date"]])
        elif r["adhik"]: adh[-1][2] = r["date"]
    y.adhik = adh
    tick(85, "पूर्ण")
    return y
