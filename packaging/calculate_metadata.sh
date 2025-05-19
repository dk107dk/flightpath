

# Calculate MD5 hash
echo -e '\ncalculating MD5...\n'
md5 ./pkg/FlightPath-Data.pkg

PKG_MD5=$(md5sum "./pkg/FlightPath-Data.pkg" | awk '{print $1}')
export PKG_MD5

# Get file size in bytes
echo -e '\ncalculating package byte size...\n'
ls -l ./pkg/FlightPath-Data.pkg | awk '{print $5}'

PKG_SIZE=$(ls -l ./pkg/FlightPath-Data.pkg | awk '{print $5}')
export PKG_SIZE

echo -e '\nthese values go into metadata.xml within 6745823097.itmsp.\n'

xml="<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<package xmlns=\"http://apple.com/itunes/importer\" version=\"software5.10\">
    <provider>Q6VE7XAQF3</provider>
    <software_assets apple_id=\"6745823097\">
        <asset type=\"product-archive\">
            <data_file>
                <file_name>FlightPath-Data.pkg</file_name>
                <checksum type=\"md5\">$PKG_MD5</checksum>
                <size>$PKG_SIZE</size>
            </data_file>
        </asset>
    </software_assets>
</package>"
echo "$xml" > ./6745823097/metadata.xml

if [ -f "6745823097.itmsp" ]; then
  echo ".itmsp exists."
else
  mv ./6745823097 ./6745823097.itmsp
fi

