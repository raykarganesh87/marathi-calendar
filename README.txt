MARATHI PANCHANG CALENDAR MAKER
===============================
Enter a year -> get a complete Marathi calendar PDF (A4 portrait, ad space at top and bottom of every page):
 * Cover: Shaka / Samvatsara / Vikram / Hijri years, holidays, sankrantis, eclipses, adhik masa notice
 * 12 month grids: Marathi dates, tithi, nakshatra, festivals (red), vratas (blue), monthly vrata summary
 * 12 daily panchang tables: tithi, nakshatra, yoga, karana, moon sign with end times, sunrise/sunset, Hijri date
 * Full-year list of ekadashi, sankashti (moonrise), vinayaki, pradosh, shivratri, pournima, amavasya
Works for any year 1900-2100 and for 25+ places (or your own latitude/longitude).

HOW TO GET THE .EXE  (a Windows .exe has to be built on Windows - two easy ways)
---------------------------------------------------------------------------------
A) On your own Windows PC:  install Python 3.12 (python.org, tick "Add to PATH"),
   then double-click  build_exe.bat .  After ~3 minutes you get  dist\MarathiCalendarMaker.exe
   (a single file; copy it anywhere, no Python needed to run it).

B) Without installing anything: upload this folder to a free GitHub repository,
   open Actions -> "Build Windows EXE" -> Run workflow, then download the .exe from the run.

USING THE PROGRAM
-----------------
Double-click MarathiCalendarMaker.exe -> enter Year, choose Place, set ad sizes (mm), press "Create Calendar PDF".
Command line also works:   MarathiCalendarMaker.exe 2028 --city Pune --out C:\cal\2028.pdf
Without building an exe you can run:  python run.py   (after  pip install -r requirements.txt)

HOW IT CALCULATES
-----------------
Swiss Ephemeris (planetary positions, Lahiri/Chitrapaksha ayanamsa) -> tithi, nakshatra, yoga, karana, moon sign,
sunrise/sunset/moonrise for the chosen place, amanta lunar months with adhik masa, sankrantis, eclipses.
Festival dates use the standard dharmashastra rules (sunrise / madhyahna / aparahna / pradosh / nishita /
moonrise, Bhadra avoidance for Holi and Rakshabandhan).
Accuracy check (tests\verify.py, runs automatically in the build): 2024-2026 key festivals match published
panchang dates, and the 2026 adhik Jyeshtha month (17 May - 15 Jun) is found correctly.

IMPORTANT LIMITS
----------------
* Where a tithi spans two days or is skipped, printed Marathi panchangs can legitimately differ
  (e.g. Lakshmi Pujan 2025: 20 vs 21 Oct). Cross-check religious dates with your preferred printed panchang.
* Islamic dates are estimates from moon visibility (+/-1 day); they are marked with *.
* Kshaya masa (very rare) and wedding/travel muhurtas, choghadiya, lagna are not included.
* The bundled font (Noto Sans Devanagari, SIL Open Font License) is embedded in the PDF.
