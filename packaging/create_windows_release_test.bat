:: 
:: don't run this script directly. instead run the create_windows_release.ps1 in an admin powershell terminal.
:: 

RD /S /Q c:\dev\flightpath\packaging\dist

poetry run pyinstaller FlightPath-Data-windows.spec

:: RD /S /Q c:\dev\flightpath\packaging\dist\FlightPathData

mkdir c:\dev\flightpath\packaging\dist\FlightPathData

move c:\dev\flightpath\packaging\dist\FlightPathData.exe c:\dev\flightpath\packaging\dist\FlightPathData

copy c:\dev\flightpath\packaging\assets\AppxManifest.xml c:\dev\flightpath\packaging\dist\FlightPathData
copy c:\dev\flightpath\packaging\assets\logo44x44.png c:\dev\flightpath\packaging\dist\FlightPathData
copy c:\dev\flightpath\packaging\assets\logo150x150.png c:\dev\flightpath\packaging\dist\FlightPathData
copy c:\dev\flightpath\packaging\assets\logo.png c:\dev\flightpath\packaging\dist\FlightPathData

C:\"Program Files (x86)"\"Windows Kits"\10\bin\10.0.26100.0\arm64\makeappx pack /d C:\dev\flightpath\packaging\dist\FlightPathData /p C:\dev\flightpath\packaging\dist\FlightPathData-test-arm64.msix

