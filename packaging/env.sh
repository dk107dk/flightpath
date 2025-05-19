

# Define the current build version
FLIGHTPATH_BUILD=$(cat build_number.txt)
#
#FLIGHTPATH_BUILD="1.0.04"
#export FLIGHTPATH_BUILD=1.0.04
#
# Extract the major, minor, and build components
IFS='.' read -r major minor build <<< "$FLIGHTPATH_BUILD"

# Increment the build number
build=$((build + 1))

# Construct the new version string
FLIGHTPATH_BUILD="$major.$minor.$build"

echo "Updated build number: $FLIGHTPATH_BUILD"

echo $FLIGHTPATH_BUILD > "build_number.txt"
cp build_number.txt ../flightpath/assets/build_number.txt

export FLIGHTPATH_BUILD

