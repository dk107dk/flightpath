#
# in this script we are code-signing with the independent distribution
# certificate. that is correct for notarizing the dmg, but it is not
# right for notarizing the pkg for the app store.
#
# for now the initial passwords and identitifers are fine. mid-term
# we need to externalize the secrets and identifiers
#
echo -e "\nloading cert for code-sign"

security default-keychain -s flightpath.keychain
#
# TODO: see codesign_app_for_store for streamlining
#
security unlock-keychain -p $FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain
#security delete-identity -Z B986A6D4F58275808006AC62C2152F05E3A7A696
security import assets/certs/mac_app_not_store_developerID_application.p12 -k flightpath.keychain -P $FLIGHTPATH_KEYCHAIN_PASSWORD -T /usr/bin/codesign
security set-key-partition-list -S apple-tool:,apple:,codedign: -s -k $FLIGHTPATH_KEYCHAIN_PASSWORD flightpath.keychain

echo -e "\nsigning app"

codesign \
    --force \
    --deep \
    --options=runtime \
    --entitlements ./assets/entitlements.plist \
    --sign "${CERT_COMMON_NAME:q}" \
    --timestamp \
    ./tmp/FlightPath\ Data.app

echo -e "\nverifing code-signed app"

codesign -vvv --deep --strict ./tmp/FlightPath\ Data.app

echo -e "\ndeleting cert code-sign cert"

#security delete-identity -Z B986A6D4F58275808006AC62C2152F05E3A7A696

security default-keychain -s login.keychain

