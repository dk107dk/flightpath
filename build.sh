
echo 'Copying FlightPath Server to local'
cp ../flightpath_server/builds/*.tar.gz ./assets
echo 'Building FlightPath Data'
#
# don't do this. be more discriminating about updates.
#
#poetry update
poetry build

cp dist/*.whl builds
cp dist/*.tar.gz builds


