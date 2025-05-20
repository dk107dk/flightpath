#
# run this script from ./packaging
#
echo -e '\nclearing...\n'
rm -Rf ./build/*
rm -Rf ./dist/*
rm -Rf ./dmg/*
rm -Rf ./pkg/*
rm -Rf ./tmp/*

echo -e '\nupdate build number...\n'
. ./env.sh

echo -e '\nbuilding installer...\n'
#
# the ID hash needs to be the developer's not the installer creator's ID
#
poetry run pyinstaller ./FlightPath\ Data-no-codesign.spec
#
#building runs CsvPath so the usual project stuff gets created
#
rm -Rf ./transfers
rm -Rf ./logs
rm -Rf ./cache
rm -Rf ./archive
rm -Rf ./config
rm -Rf ./inputs

#
# move to another dir. this was a Claude suggestion. make a difference? but doesn't hurt.
# and if we don't do it we are using the dist dir with other build artifacts or deleting
# those artifacts. we switched to copying because we can reuse the app with the pkg version
# if we want to.
#
echo -e '\ncopying app to tmp for next steps\n'
cp -R ./dist/FlightPath\ Data.app ./tmp/FlightPath\ Data.app

#
# codesign and validtion. code signing can be done by pyinstaller, but we (may) need
# the force and deep flags
#
source ./codesign_app_for_store.sh

#
# create pkg
#
echo -e '\ncreating package...\n'
. ./pkg.sh

#
# next:
#   - use calculate.sh
#   - manually setup the .itmsp
#   - use ./transport.sh to upload
#

#
# ship to apple
#
echo -e '\ntransporting .itmsp file to apple...\n'
source ./transport.sh

#
# clean up to help prevent junk from going into git
#
cd ..
. ./cleaner.sh


