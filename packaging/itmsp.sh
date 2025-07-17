#
# Step: prep itmsp file
#
echo -e '\nprepping .itmsp file for update metadata.xml\n'
rm -Rf 6745823097
rm -Rf 6745823097.itmsp
mkdir clean_itmsp
#mv ./6745823097.itmsp ./6745823097
#rm ./6745823097/FlightPath-Data.pkg
#rm ./6745823097/metadata.xml
cp ./pkg/FlightPath-Data.pkg ./clean_itmsp

#
#   - update the metadata.xml
. ./calculate_metadata.sh
#
#   - close the .itmsp
#   this causes an mv error because why? seems to work, tho.
mv ./clean_itmsp ./6745823097.itmsp


