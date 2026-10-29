import os, sys, threading, queue, datetime as dt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .places import PLACES
from . import render


def default_dir():
    d = os.path.join(os.path.expanduser("~"), "Documents")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def main():
    root = tk.Tk()
    root.title("Marathi Panchang Calendar Maker")
    root.resizable(False, False)
    pad = dict(padx=8, pady=4)
    frm = ttk.Frame(root, padding=12); frm.grid()

    ttk.Label(frm, text="Marathi Panchang Calendar Maker", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", **pad)
    ttk.Label(frm, text="Enter a year – the full Marathi calendar PDF (A4 portrait, ad space top & bottom) is calculated automatically.",
              wraplength=520, foreground="#555").grid(row=1, column=0, columnspan=4, sticky="w", **pad)

    ttk.Label(frm, text="Year").grid(row=2, column=0, sticky="e", **pad)
    year_var = tk.StringVar(value=str(dt.date.today().year + (1 if dt.date.today().month >= 7 else 0)))
    ttk.Spinbox(frm, from_=1900, to=2100, textvariable=year_var, width=8).grid(row=2, column=1, sticky="w", **pad)

    ttk.Label(frm, text="Place").grid(row=3, column=0, sticky="e", **pad)
    names = [p[0] for p in PLACES] + ["Custom (enter latitude / longitude)"]
    place_var = tk.StringVar(value=names[0])
    cb = ttk.Combobox(frm, textvariable=place_var, values=names, state="readonly", width=38)
    cb.grid(row=3, column=1, columnspan=3, sticky="w", **pad)

    ttk.Label(frm, text="Custom place name (Marathi)").grid(row=4, column=0, sticky="e", **pad)
    cname = tk.StringVar(value="")
    e1 = ttk.Entry(frm, textvariable=cname, width=18); e1.grid(row=4, column=1, sticky="w", **pad)
    ttk.Label(frm, text="Lat / Lon").grid(row=4, column=2, sticky="e", **pad)
    lat_var, lon_var = tk.StringVar(value="19.9975"), tk.StringVar(value="73.7898")
    f2 = ttk.Frame(frm); f2.grid(row=4, column=3, sticky="w")
    e2 = ttk.Entry(f2, textvariable=lat_var, width=9); e2.pack(side="left", padx=(0, 4))
    e3 = ttk.Entry(f2, textvariable=lon_var, width=9); e3.pack(side="left")
    custom_widgets = (e1, e2, e3)
    def on_place(*_):
        st = "normal" if place_var.get().startswith("Custom") else "disabled"
        for w in custom_widgets: w.configure(state=st)
    cb.bind("<<ComboboxSelected>>", on_place); on_place()

    ttk.Separator(frm).grid(row=5, column=0, columnspan=4, sticky="ew", pady=6)
    ttk.Label(frm, text="Advertisement space (mm) – 0 = none", font=("Segoe UI", 9, "bold")).grid(row=6, column=0, columnspan=4, sticky="w", **pad)
    ad_vars = {}
    def ad_row(r, label, k1, k2, d1, d2):
        ttk.Label(frm, text=label).grid(row=r, column=0, sticky="e", **pad)
        ad_vars[k1], ad_vars[k2] = tk.StringVar(value=str(d1)), tk.StringVar(value=str(d2))
        f = ttk.Frame(frm); f.grid(row=r, column=1, columnspan=3, sticky="w", **pad)
        ttk.Label(f, text="Top").pack(side="left")
        ttk.Spinbox(f, from_=0, to=80, textvariable=ad_vars[k1], width=5).pack(side="left", padx=(4, 14))
        ttk.Label(f, text="Bottom").pack(side="left")
        ttk.Spinbox(f, from_=0, to=80, textvariable=ad_vars[k2], width=5).pack(side="left", padx=4)
    ad_row(7, "Month calendar pages", "gt", "gb", 28, 28)
    ad_row(8, "Daily panchang / other pages", "ot", "ob", 20, 20)

    ttk.Separator(frm).grid(row=9, column=0, columnspan=4, sticky="ew", pady=6)
    ttk.Label(frm, text="Save as").grid(row=10, column=0, sticky="e", **pad)
    out_var = tk.StringVar(value=os.path.join(default_dir(), f"Marathi_Panchang_Calendar_{year_var.get()}.pdf"))
    ttk.Entry(frm, textvariable=out_var, width=44).grid(row=10, column=1, columnspan=2, sticky="w", **pad)
    def browse():
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=os.path.basename(out_var.get()),
                                         initialdir=os.path.dirname(out_var.get()))
        if p: out_var.set(p)
    ttk.Button(frm, text="Browse…", command=browse).grid(row=10, column=3, sticky="w", **pad)
    def sync_name(*_):
        d, f = os.path.split(out_var.get())
        if f.startswith("Marathi_Panchang_Calendar_"):
            out_var.set(os.path.join(d, f"Marathi_Panchang_Calendar_{year_var.get()}.pdf"))
    year_var.trace_add("write", sync_name)

    open_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(frm, text="Open the PDF when finished", variable=open_var).grid(row=11, column=1, columnspan=3, sticky="w", **pad)

    prog = ttk.Progressbar(frm, length=520, maximum=100); prog.grid(row=12, column=0, columnspan=4, **pad)
    status = tk.StringVar(value="Ready."); ttk.Label(frm, textvariable=status, foreground="#444").grid(row=13, column=0, columnspan=4, sticky="w", **pad)
    btn = ttk.Button(frm, text="Create Calendar PDF"); btn.grid(row=14, column=0, columnspan=4, pady=8)

    q = queue.Queue()
    def worker(args):
        try:
            year, lat, lon, place, path, ad_grid, ad_other = args
            render.make_pdf(year, lat, lon, place, path, ad_grid, ad_other, progress=lambda p, m="": q.put(("p", p, m)))
            q.put(("done", path))
        except Exception as ex:
            import traceback
            q.put(("err", f"{ex}\n\n{traceback.format_exc()}"))

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == "p":
                    prog["value"] = m[1]; status.set("Working… " + str(int(m[1])) + "%")
                elif m[0] == "done":
                    btn.configure(state="normal"); prog["value"] = 100; status.set("Done: " + m[1])
                    if open_var.get():
                        try:
                            if sys.platform.startswith("win"): os.startfile(m[1])
                            elif sys.platform == "darwin": os.system(f'open "{m[1]}"')
                            else: os.system(f'xdg-open "{m[1]}" >/dev/null 2>&1 &')
                        except Exception: pass
                elif m[0] == "err":
                    btn.configure(state="normal"); status.set("Error"); messagebox.showerror("Error", m[1])
        except queue.Empty:
            pass
        root.after(100, poll)

    def go():
        try:
            year = int(year_var.get())
            if not 1900 <= year <= 2100: raise ValueError
        except ValueError:
            messagebox.showerror("Year", "Please enter a year between 1900 and 2100."); return
        sel = place_var.get()
        if sel.startswith("Custom"):
            try: lat, lon = float(lat_var.get()), float(lon_var.get())
            except ValueError:
                messagebox.showerror("Place", "Latitude / longitude must be numbers (e.g. 19.9975, 73.7898)."); return
            place = cname.get().strip() or "स्थानिक"
        else:
            p = next(p for p in PLACES if p[0] == sel); place, lat, lon = p[1], p[2], p[3]
        try:
            ad_grid = (float(ad_vars["gt"].get()), float(ad_vars["gb"].get()))
            ad_other = (float(ad_vars["ot"].get()), float(ad_vars["ob"].get()))
        except ValueError:
            messagebox.showerror("Advertisement space", "Ad sizes must be numbers (mm)."); return
        path = out_var.get().strip()
        if not path: browse(); path = out_var.get()
        btn.configure(state="disabled"); prog["value"] = 0; status.set("Starting…")
        threading.Thread(target=worker, args=((year, lat, lon, place, path, ad_grid, ad_other),), daemon=True).start()
    btn.configure(command=go)
    poll()
    root.mainloop()
