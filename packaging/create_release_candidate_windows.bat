echo 'clearing old stuff'
rmdir /S /Q build
mkdir build
mkdir dist
rmdir /S /Q tmp
mkdir tmp

rem rmdir /S /Q dist
rem echo 'building installer'
rem poetry run pyinstaller FlightPath-Data-windows.spec

echo 'cleaning up'
rmdir /S /Q transfers
rmdir /S /Q logs
rmdir /S /Q cache
rmdir /S /Q archive
rmdir /S /Q config
rmdir /S /Q inputs

C:\"Program Files (x86)"\"Windows Kits"\10\bin\10.0.26100.0\arm64\makeappx pack /d C:\dev\flightpath\packaging\dist\FlightPath_Data /p FlightPath_Data.msix
