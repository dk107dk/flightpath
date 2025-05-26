#
# run this script from ./packaging
#
echo '\nclearing old stuff\n'
rmdir /S /Q dist build/*
rmdir /S /Q dist dist/*
rmdir /S /Q dist dmg/*
rmdir /S /Q dist pkg/*
rmdir /S /Q dist tmp/*

echo '\nbuilding installer\n'
#
# windows spec is exactly like the macos spec. to join them we just need to lose the space.
# will do that from the macos side.
#
poetry run pyinstaller FlightPath-Data-windows.spec

#
# building runs CsvPath so the usual project stuff gets created
#
echo '\ncleaning up\n'
rmdir /S /Q dist transfers
rmdir /S /Q dist logs
rmdir /S /Q dist cache
rmdir /S /Q dist archive
rmdir /S /Q dist config
rmdir /S /Q dist inputs

