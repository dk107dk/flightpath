
#
# notarize
#
xcrun notarytool submit ./dmg/FlightPath\ Data.dmg \
        --keychain-profile notarytool \
        --wait

#
# staple for dist
#
echo -e '\nwait 30 seconds for notarization ticket'
sleep 30

echo -e '\nstaple file'
xcrun stapler staple ./dmg/FlightPath\ Data.dmg

