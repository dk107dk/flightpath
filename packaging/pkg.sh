#
# Step 1: Create a component package first
#
echo -e '\ndoing pkgbuild to create pkg...\n'
pkgbuild --component ./tmp/FlightPath\ Data.app \
         --install-location "/Applications" \
         --identifier com.flightpathdata.flightpath \
         --version 1.0.02 \
         ./pkg/component.pkg
#
# Step 2: Build the final package with productbuild
#
echo -e '\ndoing productbuild with pkg to create distribution...\n'
security unlock-keychain -p @env:FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain
productbuild --product ./assets/product_definition.plist \
             --package-path ./pkg \
             --identifier com.flightpathdata.flightpath \
             --version 1.0.01 \
             --sign @env:CERT_COMMON_NAME \
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
cp ./pkg/FlightPath-Data.pkg ./6745823097
source ./calculate_metadata.sh
#
# Next:
#   - update the metadata.xml
#   - close the .itmsp
#   - run transport.sh
#
