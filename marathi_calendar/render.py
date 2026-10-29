"""
PDF renderer: A4 portrait Marathi panchang calendar with advertisement space.

Pure-Python stack (fpdf2 + uharfbuzz) so it bundles cleanly into a Windows .exe.
All text is drawn with FPDF.cell(), which applies HarfBuzz shaping (needed for Devanagari).
"""
import os, sys, datetime as dt
from fpdf import FPDF
from . import engine as E
from .engine import dn

PW, PH, M = 210.0, 297.0, 6.0          # page, margin (mm)
CW = PW - 2 * M                          # content width = 198

MAROON = (122, 31, 31); GOLD = (255, 210, 122); RED = (179, 18, 27); BLUE = (11, 79, 138)
INK = (42, 26, 18); GREY = (110, 110, 110); LINE = (185, 165, 143)
PINK = (253, 234, 234); YEL = (255, 246, 207); LAV = (233, 230, 238); BEIGE = (244, 239, 233)
ORANGE = (242, 163, 58); SUNRED = (199, 42, 42)


def resource_path(rel):
    here = os.path.dirname(os.path.abspath(__file__))
    cands = []
    if getattr(sys, "_MEIPASS", None):
        cands.append(os.path.join(sys._MEIPASS, "marathi_calendar", rel))
        cands.append(os.path.join(sys._MEIPASS, rel))
    cands.append(os.path.join(here, rel))
    for c in cands:
        if os.path.exists(c): return c
    raise FileNotFoundError(rel)


def S(t):
    """Replace characters that Noto Sans Devanagari has no glyph for."""
    return (t.replace("·", "|").replace("▸", "-").replace("•", "-").replace("°", "").replace("&", "आणि")
             .replace("≈", "~").replace("→", "-"))


class Cal:
    def __init__(self, y, ad_grid=(28, 28), ad_other=(20, 20), progress=None):
        self.y = y
        self.ad_grid, self.ad_other = ad_grid, ad_other
        self.progress = progress
        p = FPDF("P", "mm", "A4")
        p.set_auto_page_break(False)
        p.set_margins(0, 0, 0)
        p.c_margin = 0
        p.add_font("NSD", "", resource_path("fonts/NotoSansDevanagari-Regular.ttf"))
        p.add_font("NSD", "B", resource_path("fonts/NotoSansDevanagari-Bold.ttf"))
        p.set_text_shaping(True)
        p.set_title(S(f"मराठी पंचांग दिनदर्शिका {dn(y.year)}"))
        p.set_creator("Marathi Calendar Maker")
        self.p = p

    # ---------------------------------------------------------- primitives
    def font(self, size, bold=False):
        self.p.set_font("NSD", "B" if bold else "", size)

    def tw(self, txt, size, bold=False):
        self.font(size, bold)
        return self.p.get_string_width(txt)

    def put(self, x, y, txt, size=7, bold=False, color=INK, w=None, align="L"):
        """Draw text with its line box starting at (x, y)."""
        if not txt: return 0
        self.font(size, bold)
        self.p.set_text_color(*color)
        lh = size * 0.3528 * 1.4
        width = self.p.get_string_width(txt)
        box = w if w is not None else width + 0.3
        self.p.set_xy(x, y)
        self.p.cell(box, lh, txt, align=align)
        return width

    def fit(self, txt, w, size, bold=False, minsize=5.0):
        while size > minsize and self.tw(txt, size, bold) > w:
            size -= 0.2
        return size

    def put_fit(self, x, y, w, txt, size, bold=False, color=INK, align="L"):
        s = self.fit(txt, w, size, bold)
        self.put(x, y + (size - s) * 0.18, txt, s, bold, color, w=w, align=align)

    def rect(self, x, y, w, h, fill=None, line=None, lw=0.25, rounded=0):
        p = self.p
        style = ("F" if fill else "") + ("D" if line else "")
        if not style: return
        if fill: p.set_fill_color(*fill)
        if line:
            p.set_draw_color(*line); p.set_line_width(lw)
        if rounded: p.rect(x, y, w, h, style=style or "D", round_corners=True, corner_radius=rounded)
        else: p.rect(x, y, w, h, style=style)

    def flow(self, tokens, x, y, w, size, lh, maxh, clip=True):
        """tokens = [(text, color, bold)]; wraps words inside width w, stops at maxh."""
        cx, cy = x, y
        sp = self.tw(" ", size)
        ctx = self.p.rect_clip(x, y, w, maxh) if clip else None
        if ctx: ctx.__enter__()
        try:
            for text, color, bold in tokens:
                for word in text.split(" "):
                    if not word: continue
                    ww = self.tw(word, size, bold)
                    if cx > x and cx + ww > x + w + 0.01:
                        cx = x; cy += lh
                    if cy + lh > y + maxh + 0.5: return cy
                    self.put(cx, cy, word, size, bold, color)
                    cx += ww + sp
        finally:
            if ctx: ctx.__exit__(None, None, None)
        return cy

    def wrap_lines(self, text, w, size, bold=False):
        lines, cur = [], ""
        for word in text.split(" "):
            t = (cur + " " + word).strip()
            if cur and self.tw(t, size, bold) > w:
                lines.append(cur); cur = word
            else:
                cur = t
        if cur: lines.append(cur)
        return lines

    def ad_box(self, x, y, w, h):
        if h <= 0: return
        p = self.p
        self.rect(x, y, w, h, fill=(250, 248, 245))
        p.set_draw_color(150, 140, 130); p.set_line_width(0.35)
        p.set_dash_pattern(dash=1.6, gap=1.2); p.rect(x, y, w, h); p.set_dash_pattern()
        label = S(f"येथे जाहिरात द्या ({dn(int(w))} × {dn(int(h))} मिमी)")
        s = 8
        tw_ = self.tw(label, s)
        self.put(x + (w - tw_) / 2, y + h / 2 - s * 0.3528 * 0.7, label, s, color=(165, 155, 145))

    def new_page(self, ad):
        self.p.add_page()
        top, bot = ad
        self.ad_box(M, M, CW, top)
        self.ad_box(M, PH - M - bot, CW, bot)
        y0 = M + top + (2 if top else 0)
        y1 = PH - M - bot - (2 if bot else 0)
        return y0, y1

    def bar(self, y, h, left, right_lines=(), left_size=22, year_txt=None):
        self.rect(M, y, CW, h, fill=MAROON, rounded=2)
        wl = self.put(M + 4, y + (h - left_size * 0.3528 * 1.4) / 2 - 0.3, left, left_size, True, (255, 255, 255))
        if year_txt:
            self.put(M + 4 + wl + 2, y + h / 2 - 1.2, year_txt, 11, True, GOLD)
        n = len(right_lines)
        if n:
            lh = 3.6
            ty = y + (h - n * lh) / 2
            for i, ln in enumerate(right_lines):
                self.put(M + 4, ty + i * lh, ln, 7.2, False, (255, 255, 255), w=CW - 8, align="R")

    # ---------------------------------------------------------- helpers
    def T(self, jd, day):
        t = E.to_ist(jd)
        s = f"{t.hour:02d}:{t.minute:02d}" + ("*" if t.date() > day else "")
        return dn(s)

    @staticmethod
    def tithi_short(n):
        if n == 15: return "पौर्णिमा"
        if n == 30: return "अमावास्या"
        return ("शु. " if n <= 15 else "व. ") + dn((n - 1) % 15 + 1)

    # ---------------------------------------------------------- pages
    def cover(self):
        y = self.y
        y0, y1 = self.new_page(self.ad_other)
        self.rect(M, y0, CW, 44, fill=MAROON, rounded=3)
        self.put(M + 8, y0 + 2.5, dn(y.year), 44, True, GOLD)
        self.put(M + 8, y0 + 21, "मराठी पंचांग दिनदर्शिका", 24, True, (255, 255, 255))
        d0, d1 = y.days[0]["date"], y.days[-1]["date"]
        sa, sb = y.shaka_of(d0), y.shaka_of(d1)
        sv = y.samvatsara_of(d0), y.samvatsara_of(d1)
        shk = dn(sa) if sa == sb else f"{dn(sa)}–{dn(sb)}"
        vs = dn(sa + 135) if sa == sb else f"{dn(sa + 135)}–{dn(sb + 135)}"
        smv = sv[0] if sv[0] == sv[1] else f"{sv[0]} / {sv[1]}"
        hy0, hy1 = y.days[0]["hijri"][2], y.days[-1]["hijri"][2]
        hj = dn(hy0) if hy0 == hy1 else f"{dn(hy0)}–{dn(hy1)}"
        self.put(M + 8, y0 + 32.5, S(f"शके {shk} | {smv} संवत्सर | विक्रम संवत {vs} | हिजरी {hj}"), 9.5, False, (255, 255, 255))
        g = y.gudi
        self.put(M + 8, y0 + 37.8, S(f"शके {dn(y.shaka_of(g))} चा प्रारंभ: गुढीपाडवा, {dn(g.day)} {E.GREG[g.month-1]} {dn(g.year)}   |   स्थळ: {y.place}"),
                 8.2, False, GOLD)
        colw = (CW - 5) / 2
        top = y0 + 49
        # holidays
        self.put(M, top, "सुट्ट्या व प्रमुख सण", 9.5, True, MAROON)
        self.rect(M, top + 5.4, colw, 0.4, fill=ORANGE)
        yy = top + 7
        hol = []
        for r in y.days:
            if r["holiday"]:
                txt = "; ".join(x for x in r["fest"] if "संक्रांत" not in x and "मास प्रारंभ" not in x and "शब-ए" not in x)
                if txt: hol.append((r["date"], txt))
        lh = 3.0
        for d, txt in hol:
            lines = self.wrap_lines(S(txt), colw - 33, 7)
            h = max(1, len(lines)) * lh + 0.9
            if yy + h > y1: break
            self.put(M + 0.5, yy, f"{dn(d.day)} {E.GREG[d.month-1]}", 7, True)
            self.put(M + 22, yy, E.WEEK_S[d.weekday()], 7, False, GREY)
            for i, ln in enumerate(lines):
                self.put(M + 32, yy + i * lh, ln, 7, False)
            yy += h
            self.rect(M, yy - 0.25, colw, 0.12, fill=(217, 205, 191))
        # right column
        rx = M + colw + 5
        ry = top
        self.put(rx, ry, "संक्रांती (सूर्याचा राशीप्रवेश)", 9.5, True, MAROON)
        self.rect(rx, ry + 5.4, colw, 0.4, fill=ORANGE)
        ry += 7
        for ist, ri in y.sank:
            self.put(rx + 0.5, ry, f"{E.RASHI[ri]} संक्रांत", 7)
            self.put(rx + 0.5, ry, f"{dn(ist.day)} {E.GREG[ist.month-1]}, {dn(ist.strftime('%H:%M'))}", 7, w=colw - 1, align="R")
            ry += 3.4
        ry += 3
        self.put(rx, ry, f"ग्रहणे {dn(y.year)}", 9.5, True, MAROON)
        self.rect(rx, ry + 5.4, colw, 0.4, fill=ORANGE)
        ry += 7
        if not y.ecl:
            self.put(rx + 0.5, ry, "या वर्षात ग्रहण नाही", 7); ry += 3.4
        for e in y.ecl:
            lab = y.ecl_label(e)
            vis = "दिसेल" if e[3] else "दिसणार नाही"
            self.put(rx + 0.5, ry, lab, 7, True)
            self.put(rx + 0.5, ry, S(f"{dn(e[1].day)} {E.GREG[e[1].month-1]}, {dn(e[1].strftime('%H:%M'))} | {y.place}: {vis}"),
                     6.8, False, GREY, w=colw - 1, align="R")
            ry += 3.4
        ry += 3
        self.put(rx, ry, "माहिती व टीप", 9.5, True, MAROON)
        self.rect(rx, ry + 5.4, colw, 0.4, fill=ORANGE)
        ry += 7
        adh = "या वर्षात अधिक मास नाही."
        if y.adhik:
            adh = "अधिक मास: " + "; ".join(f"अधिक {E.MMONTH[m]} ({dn(a.day)} {E.GREG[a.month-1]} ते {dn(b.day)} {E.GREG[b.month-1]})" for m, a, b in y.adhik) + "."
        notes = [
            f"तिथी, नक्षत्र, योग, करण, चंद्र राशी व सूर्योदय/सूर्यास्त खगोलीय गणिताने (लाहिरी/चित्रपक्ष अयनांश) {y.place} साठी काढले आहेत. वेळा भारतीय प्रमाणवेळ, २४ तासांत; * = पुढील दिवशी.",
            "महिने अमांत पद्धतीचे (अमावास्येला महिना संपतो). " + adh,
            "सण-तिथी निर्णय प्रचलित धर्मशास्त्र नियमांनुसार (सूर्योदय / मध्याह्न / अपराह्न / प्रदोष / निशीथ / चंद्रोदय, भद्रा परिहार) संगणकाद्वारे ठरवले आहेत. तिथी दोन दिवस किंवा क्षय असल्यास छापील पंचांगांत मतभेद संभवतात (उदा. लक्ष्मीपूजन).",
            "* खूण असलेले इस्लामी सण चंद्रदर्शनावर अवलंबून; हिजरी तारखा अंदाजित, ±१ दिवस फरक शक्य.",
            "मुहूर्त / लग्न / चौघडिया समाविष्ट नाहीत. धार्मिक कार्यासाठी स्थानिक पंचांगाशी पडताळणी करावी.",
        ]
        for n in notes:
            for ln in self.wrap_lines(S("- " + n), colw, 6.6):
                if ry + 3 > y1: break
                self.put(rx, ry, ln, 6.6, False, INK); ry += 2.9
            ry += 0.8

    def month(self, m):
        y = self.y
        recs = [r for r in y.days if r["date"].month == m]
        first, last = recs[0], recs[-1]
        names = []
        for r in recs:
            nm = ("अधिक " if r["adhik"] else "") + E.MMONTH[r["month"]]
            if nm not in names: names.append(nm)
        sa, sb = y.shaka_of(first["date"]), y.shaka_of(last["date"])
        shk = dn(sa) if sa == sb else f"{dn(sa)}–{dn(sb)}"
        sv = y.samvatsara_of(first["date"]); sv2 = y.samvatsara_of(last["date"])
        smv = sv if sv == sv2 else f"{sv} / {sv2}"
        hj = sorted({(r["hijri"][1], r["hijri"][2]) for r in recs}, key=lambda x: (x[1], x[0]))
        hj_s = " – ".join(E.HIJRI_M[a] for a, b in hj) + f" {dn(hj[-1][1])}"
        vs = dn(sa + 135) + ("–" + dn(sb + 135) if sa != sb else "")
        self.grid_page(m, recs, names, shk, smv, hj_s, vs)
        self.table_page(m, recs)

    # ---- month grid ---------------------------------------------------
    def grid_page(self, m, recs, names, shk, smv, hj_s, vs):
        y0, y1 = self.new_page(self.ad_grid)
        hdr_h = 16
        self.bar(y0, hdr_h, E.GREG[m - 1], [S(f"{' – '.join(names)}  |  शके {shk}  |  {smv} संवत्सर"),
                                           S(f"हिजरी: {hj_s}  |  विक्रम संवत {vs}")], 22, dn(self.y.year))
        th_y = y0 + hdr_h + 1.5
        th_h = 6
        foot_h = 15
        foot_y = y1 - foot_h
        first = recs[0]
        firstwd = (first["date"].weekday() + 1) % 7
        cells = [None] * firstwd + recs
        while len(cells) % 7: cells.append(None)
        rows = len(cells) // 7
        top = th_y + th_h
        rowh = (foot_y - 1.2 - top) / rows
        cw = CW / 7
        # weekday header
        for i, nm in enumerate(["रविवार", "सोमवार", "मंगळवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"]):
            x = M + i * cw
            self.rect(x, th_y, cw, th_h, fill=SUNRED if i == 0 else ORANGE, line=(161, 90, 0))
            s = 7.8
            tw_ = self.tw(nm, s, True)
            self.put(x + (cw - tw_) / 2, th_y + 1.0, nm, s, True, (255, 255, 255) if i == 0 else (58, 21, 0))
        for ri in range(rows):
            for ci in range(7):
                c = cells[ri * 7 + ci]
                x, yy = M + ci * cw, top + ri * rowh
                if c is None:
                    self.rect(x, yy, cw, rowh, fill=BEIGE, line=LINE)
                else:
                    self.day_cell(c, x, yy, cw, rowh)
        self.footer(recs, M, foot_y, CW, foot_h)

    def day_cell(self, r, x, y, w, h):
        d = r["date"]; n = r["tithi"]
        hol = r["holiday"] or r["wd"] == 6
        fill = None
        if r["holiday"]: fill = PINK
        if n == 15: fill = YEL
        if n == 30: fill = LAV
        self.rect(x, y, w, h, fill=fill or (255, 255, 255), line=LINE)
        col = RED if hol else INK
        big = dn(d.day)
        bw = self.put(x + 1.1, y + 0.4, big, 17, True, col)
        self.put(x + 1.1 + bw + 0.9, y + 4.2, str(d.day), 6.5, True, (125, 125, 125))
        ts = self.tithi_short(n)
        tsw = self.tw(ts, 7, True)
        self.put(x + w - 1.1 - tsw, y + 1.1, ts, 7, True, MAROON)
        if n in (15, 30):
            self.p.set_draw_color(138, 106, 0); self.p.set_line_width(0.3)
            self.p.set_fill_color(255, 224, 102) if n == 15 else self.p.set_fill_color(51, 51, 51)
            self.p.ellipse(x + w - 1.1 - tsw - 3.0, y + 1.7, 2.3, 2.3, style="DF")
        self.put_fit(x + 1.1, y + 7.3, w - 2.2, E.tithi_name(n), 7.6, True)
        self.put_fit(x + 1.1, y + 10.8, w - 2.2, E.NAK[r["nak"]], 6.8, False, GREY)
        toks = []
        items = [(S(t), RED, True) for t in r["fest"]] + \
                [(S(t), BLUE, False) for t in r["vrata"] if t not in ("पौर्णिमा", "अमावास्या")]
        for i, (t, c, b) in enumerate(items):
            if i: toks.append(("|", (150, 150, 150), False))
            toks.append((t, c, b))
        self.flow(toks, x + 1.1, y + 14.2, w - 2.0, 6.6, 2.85, h - 14.4 - 0.4)

    def footer(self, recs, x, y, w, h):
        dd = dn
        ek = [r for r in recs if any("एकादशी" in t for t in r["vrata"])]
        ekt = "; ".join(f'{dd(r["date"].day)} {[t for t in r["vrata"] if "एकादशी" in t][0].replace(" एकादशी", "").replace("एकादशी", "")}'.strip() for r in ek)
        sk = " ".join(dd(r["date"].day) for r in recs if any("संकष्ट" in t for t in r["vrata"]))
        vi = " ".join(dd(r["date"].day) for r in recs if "विनायकी चतुर्थी" in r["vrata"])
        pr = ", ".join(f'{dd(r["date"].day)} ({t.split()[0]})' for r in recs for t in r["vrata"] if "प्रदोष" in t)
        ms = " ".join(dd(r["date"].day) for r in recs if any("मासिक शिवरात्री" in t for t in r["vrata"]))
        pu = " ".join(dd(r["date"].day) for r in recs if "पौर्णिमा" in r["vrata"])
        am = " ".join(dd(r["date"].day) for r in recs if "अमावास्या" in r["vrata"])
        a, b = recs[0], recs[-1]
        self.rect(x, y, w, 0.4, fill=MAROON)
        SEP = ("|", (150, 150, 150), False)
        def grp(label, val): return [(label + " ", MAROON, True), (val or "—", INK, False)]
        def join(*gs):
            out = []
            for i, g in enumerate(gs):
                if i: out.append(SEP)
                out += g
            return out
        lines = [
            join(grp("एकादशी:", ekt), grp("संकष्ट चतुर्थी:", sk), grp("विनायकी:", vi)),
            join(grp("प्रदोष:", pr), grp("मासिक शिवरात्री:", ms), grp("पौर्णिमा:", pu), grp("अमावास्या:", am)),
            join(grp(S(f"सूर्योदय / सूर्यास्त ({self.y.place}):"),
                     f"{dd(1)} तारीख {self.T(a['sr'], a['date'])} / {self.T(a['ss'], a['date'])}  –  "
                     f"{dd(b['date'].day)} तारीख {self.T(b['sr'], b['date'])} / {self.T(b['ss'], b['date'])}")),
        ]
        cy = y + 1.0
        for toks in lines:
            cy = self.flow(toks, x, cy, w, 6.9, 3.2, y + h - cy, clip=True) + 3.3

    # ---- daily table ----------------------------------------------------
    def table_page(self, m, recs):
        y0, y1 = self.new_page(self.ad_other)
        self.bar(y0, 11, f"{E.GREG[m-1]} {dn(self.y.year)} – दैनंदिन पंचांग", [S(f"{self.y.place} | भा.प्र.वे. २४ तास | * = पुढील दिवशी")], 14)
        yy = y0 + 11 + 1.5
        widths = [15, 37, 32, 24, 24, 22, 22, 22]
        heads = ["तारीख/वार", "तिथी (समाप्ती)", "नक्षत्र (समाप्ती)", "योग (समाप्ती)", "करण (समाप्ती)",
                 "चंद्र रास", "सूर्योदय / सूर्यास्त", "हिजरी"]
        th_h = 5.6
        x = M
        for wd, h in zip(widths, heads):
            self.rect(x, yy, wd, th_h, fill=MAROON, line=MAROON)
            self.put(x + 0.8, yy + 0.9, h, 6.8, True, (255, 255, 255))
            x += wd
        yy += th_h
        # festival text per day (pre-wrapped)
        fe, fh = {}, 2.95
        for r in recs:
            ev = [S(t) for t in r["fest"] + r["vrata"] if t not in ("पौर्णिमा", "अमावास्या")]
            if r["tithi"] in (15, 30): ev.insert(0, E.tithi_name(r["tithi"]))
            if ev: fe[r["date"]] = self.wrap_lines("- " + " | ".join(ev), CW - 5, 6.6, True)
        fest_total = sum(len(v) * fh + 1.0 for v in fe.values())
        avail = y1 - yy
        dh = min(7.2, (avail - fest_total) / len(recs))
        for r in recs:
            d = r["date"]; n = r["tithi"]
            hol = r["holiday"] or r["wd"] == 6
            fill = PINK if hol else (255, 255, 255)
            cells = [
                (f"{dn(d.day)} {E.WEEK_S[r['wd']]}", None),
                (E.tithi_full(n, r["month"], r["adhik"]), self.T(r["tithi_end"], d)),
                (E.NAK[r["nak"]], self.T(r["nak_end"], d)),
                (E.YOGA[r["yoga"]], self.T(r["yoga_end"], d)),
                (r["karana"], self.T(r["karana_end"], d)),
                (E.RASHI[r["rashi"]], self.T(r["rashi_end"], d)),
                (f"{self.T(r['sr'], d)} / {self.T(r['ss'], d)}", None),
                (f"{dn(r['hijri'][0])} {E.HIJRI_M[r['hijri'][1]]}", None),
            ]
            x = M
            for i, ((a, b), wd) in enumerate(zip(cells, widths)):
                self.rect(x, yy, wd, dh, fill=fill, line=(205, 191, 174), lw=0.2)
                ty = yy + (dh - 7.4 * 0.3528 * 1.4) / 2
                if i == 0:
                    self.put(x + 0.8, ty, a, 7.4, True)
                else:
                    size = 7.4
                    full = a + (" " + b if b else "")
                    while size > 5.0 and self.tw(a, size) + (self.tw(" " + b, size, True) if b else 0) > wd - 1.4:
                        size -= 0.2
                    wa = self.put(x + 0.8, ty + (7.4 - size) * 0.15, a, size)
                    if b: self.put(x + 0.8 + wa + self.tw(" ", size), ty + (7.4 - size) * 0.15, b, size, True)
                x += wd
            yy += dh
            if d in fe:
                lines = fe[d]
                h = len(lines) * fh + 1.0
                self.rect(M, yy, CW, h, fill=fill, line=(205, 191, 174), lw=0.2)
                for k, ln in enumerate(lines):
                    self.put(M + 3, yy + 0.5 + k * fh, ln, 6.6, True, RED)
                yy += h

    # ---- vrata list -------------------------------------------------------
    def vrata(self):
        y = self.y
        secs = {"एकादशी": [], "संकष्ट चतुर्थी (चंद्रोदय)": [], "विनायकी चतुर्थी": [], "प्रदोष": [],
                "मासिक शिवरात्री": [], "पौर्णिमा": [], "अमावास्या": []}
        for r in y.days:
            ds = f'{dn(r["date"].day)} {E.GREG[r["date"].month-1][:3]} ({E.WEEK_S[r["wd"]]})'
            for t in r["vrata"]:
                if "एकादशी" in t: secs["एकादशी"].append(f"{ds} – {t.replace(' एकादशी', '')}")
                elif "संकष्ट" in t:
                    tm = t.split("चंद्रोदय ")[1].rstrip(")") if ("चंद्रोदय " in t and "तिथी नाही" not in t) else "प्रदोष"
                    secs["संकष्ट चतुर्थी (चंद्रोदय)"].append(f"{ds} – {tm}")
                elif t == "विनायकी चतुर्थी": secs["विनायकी चतुर्थी"].append(ds)
                elif "प्रदोष" in t: secs["प्रदोष"].append(ds)
                elif "शिवरात्री" in t: secs["मासिक शिवरात्री"].append(ds)
                elif t == "पौर्णिमा": secs["पौर्णिमा"].append(ds)
                elif t == "अमावास्या": secs["अमावास्या"].append(ds)
        colw = (CW - 10) / 3
        lh = 3.45
        def start():
            y0, y1 = self.new_page(self.ad_other)
            self.bar(y0, 11, f"व्रते व उपवास – यादी {dn(y.year)}", ["स्मार्त / भागवत भेद दर्शवला आहे"], 14)
            return y0 + 11 + 3, y1
        top, y1 = start()
        col, yy = 0, top
        def advance(need):
            nonlocal col, yy, top, y1
            if yy + need > y1:
                col += 1; yy = top
                if col == 3:
                    top, y1 = start(); col, yy = 0, top
        for title, items in secs.items():
            advance(lh * 3)
            x = M + col * (colw + 5)
            self.put(x, yy, S(title), 8.5, True, MAROON)
            self.rect(x, yy + 4.8, colw, 0.3, fill=ORANGE)
            yy += 6
            for it in items:
                advance(lh)
                x = M + col * (colw + 5)
                self.put_fit(x + 0.5, yy, colw - 1, S(it), 7, False)
                yy += lh
            yy += 1.5

    # ---------------------------------------------------------- run
    def build(self, path):
        steps = ["cover"] + [m for m in range(1, 13)] + ["vrata"]
        for i, s in enumerate(steps):
            if self.progress: self.progress(86 + 13 * i / len(steps), "पीडीएफ तयार होत आहे")
            if s == "cover": self.cover()
            elif s == "vrata": self.vrata()
            else: self.month(s)
        self.p.output(path)
        if self.progress: self.progress(100, "पूर्ण")
        return path


def make_pdf(year, lat, lon, place, path, ad_grid=(28, 28), ad_other=(20, 20), progress=None):
    y = E.build(year, lat, lon, place, progress)
    return Cal(y, ad_grid, ad_other, progress).build(path)
