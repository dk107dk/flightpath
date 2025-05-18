#!/bin/sh

create-dmg \
  --volname "FlightPath Installer" \
  --volicon "../../csvpath/marketing/site/logo/flightpath/icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "FlightPath Data.app" 200 190 \
  --hide-extension "FlightPath Data.app" \
  --app-drop-link 600 185 \
  "./dmg/FlightPath Data.dmg" \
  "./tmp"



