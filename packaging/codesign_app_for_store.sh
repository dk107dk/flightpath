
#
# in this script we are code-signing for app store distribution
# with the mac_app_distribution.cer certificate
#
# for now the initial passwords and identitifers are fine. mid-term
# we need to externalize the secrets and identifiers
#

echo -e "\nloading cert for code-sign"

security default-keychain -s flightpath.keychain
security unlock-keychain -p $FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain
security set-key-partition-list -S apple-tool:,apple:,codedign: -s -k $FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain

echo -e "\nsigning app"

codesign \
    --force \
    --deep \
    --options=runtime \
    --keychain ~/Library/Keychains/flightpath.keychain-db \
    --entitlements ./assets/entitlements.plist \
    --sign "${APP_CERT_COMMON_NAME:q}" \
    --timestamp \
    ./tmp/FlightPath\ Data.app

echo -e "\nverifing code-signed app"

codesign -vvv --deep --strict ./tmp/FlightPath\ Data.app

security default-keychain -s login.keychain

