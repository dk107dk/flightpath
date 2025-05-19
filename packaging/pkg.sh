#
# Step 1: Create a component package first
#
echo "Starting pkg.sh"

FLIGHTPATH_BUILD=$(cat build_number.txt)


echo "FLIGHTPATH_BUILD: $FLIGHTPATH_BUILD"
echo "INSTALLER_CERT_COMMON_NAME: $INSTALLER_CERT_COMMON_NAME"

echo -e '\ndoing pkgbuild to create pkg...\n'
pkgbuild --component ./tmp/FlightPath\ Data.app \
         --install-location "/Applications" \
         --identifier com.flightpathdata.flightpath \
         --version $FLIGHTPATH_BUILD \
         ./pkg/component.pkg
#
# Step 2: Build the final package, including the component package
#
echo -e '\ndoing productbuild with pkg to create distribution...\n'
#echo -e "${INSTALLER_CERT_COMMON_NAME:q}"
security unlock-keychain -p $FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain
productbuild --product ./assets/product_definition.plist \
             --package-path ./pkg \
             --identifier com.flightpathdata.flightpath \
             --version $FLIGHTPATH_BUILD \
             --sign "$INSTALLER_CERT_COMMON_NAME" \
             --keychain ~/Library/Keychains/flightpath.keychain-db \
             --component ./tmp/FlightPath\ Data.app \
             /Applications \
             ./pkg/FlightPath-Data.pkg

#             --sign "3rd Party Mac Developer Installer: David Kershaw (Q6VE7XAQF3)" \

#
# Step 3: clean up
#
echo -e '\ncleaning up\n'
rm ./pkg/component.pkg
#
# Step 4: prep for itmsp file
#
echo -e '\nprepping .itmsp file for update metadata.xml\n'
mv ./6745823097.itmsp ./6745823097
rm ./6745823097/FlightPath-Data.pkg
rm ./6745823097/metadata.xml
cp ./pkg/FlightPath-Data.pkg ./6745823097
source ./calculate_metadata.sh
#
# Next:
#   - update the metadata.xml
#   - close the .itmsp
#   - run transport.sh
#
