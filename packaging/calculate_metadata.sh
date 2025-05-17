

# Calculate MD5 hash
echo -e '\ncalculating MD5...\n'
md5 ./pkg/FlightPath-Data.pkg

# Get file size in bytes
echo -e '\ncalculating package byte size...\n'
ls -l ./pkg/FlightPath-Data.pkg | awk '{print $5}'

echo -e '\nthese values go into metadata.xml within 6745823097.itmsp.\n'


