
find . -name "*.pyc" -exec rm -f {} \;

rm -R ./config
rm -R ./archive
rm -R ./cache
rm -R ./inputs
rm -R ./transfers
rm -R ./logs

rm -R ./packaging/pkg/*
rm -R ./packaging/dmg/*
rm -R ./packaging/tmp/*
rm -R ./packaging/dist/*
rm -R ./packaging/build/*
mv ./packaging/6745823097.itmsp ./packaging/6745823097
rm -R ./packaging/6745823097/*.pkg

#rm -R ~/FlightPath
#rm -R ~/.flightpath


