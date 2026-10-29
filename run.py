"""Entry point for the .exe (double-click = window; with a year argument = command line)."""
import sys
if len(sys.argv) > 1:
    from marathi_calendar.__main__ import cli
    cli(sys.argv[1:])
else:
    from marathi_calendar.gui import main
    main()
