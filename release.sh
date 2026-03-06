
#
# make this a python script. it would be a time waste to hand code it.
#

#
# check.txt holds an int. if the int is n%10==0 the splash screen is displayed.
# we do this mainly just to reshow the license link and copywrite now and then.
#
rm flightpath/assets/check.txt
echo "0" >> flightpath/assets/check.txt

. ./build.sh

echo 'Tagging FlightPath Data, FlightPath Server, and Csvpath'
cp ../flightpath_server/builds/*.tar.gz ./assets

#
# the -z is to prevent operation until a better method for managing the number
# the process should be like:
#    - get number from flightpath/assets/buildnumber.txt
#    - get attempt count from ? (can be alpha or numeric)
#    - assemble as v{number}{attempt}
#    - tag each repo
#    - push each repo
#
git tag -a -zz v1.0.86d
git push origin -zz v1.0.86d


