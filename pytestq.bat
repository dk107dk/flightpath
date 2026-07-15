@echo off
set QT_QPA_PLATFORM=offscreen
set FLIGHTPATH_SKIP_SPLASH=1
set FLIGHTPATH_SKIP_PRECACHER=1
poetry run pytest %*