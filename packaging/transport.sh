
#if [ -f "6745823097.itmsp" ]; then
#  echo ".itmsp exists."
#else
#  mv ./6745823097 ./6745823097.itmsp
#fi

#
# use calculate_metadata.sh to get the up-to-date values for metadata.xml first.
#
echo -e '\nverifying package...\n'
xcrun iTMSTransporter -m verify -f ./6745823097.itmsp -u @env:APPLE_ID -p @env:APP_SPECIFIC_PASSWORD -v detailed

echo -e '\nuploading package...\n'
xcrun iTMSTransporter -m upload -f ./6745823097.itmsp -u @env:APPLE_ID -p @env:APP_SPECIFIC_PASSWORD -v detailed



