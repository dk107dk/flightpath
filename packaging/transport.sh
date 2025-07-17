
echo -e '\nuploading package...\n'
xcrun iTMSTransporter -m upload -f ./6745823097.itmsp -u @env:APPLE_ID -p @env:APP_SPECIFIC_PASSWORD -v eXtreme


#
# this uses assetFile, but that doesn't work with .itmsp files.
# keeping it ffr. we will need to switch in the mid-term.
#
#xcrun iTMSTransporter -m upload -assetFile ./6745823097.itmsp -u @env:APPLE_ID -p @env:APP_SPECIFIC_PASSWORD -v detailed



