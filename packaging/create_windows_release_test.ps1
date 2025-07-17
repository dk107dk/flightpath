#
# if testing the installer build, run this script in powershell as administrator. 
# only this step is needed for an app submission because Microsoft will sign it with their root CA
#
c:\dev\flightpath\packaging\create_windows_release_test.bat

#
# if working on a new machine or for another reason need to create and register a new certificate on this and/or an install test machine, uncomment these three lines.
#
# New-SelfSignedCertificate -Type Custom -Subject "CN=AtestaAnalytics" -KeyUsage DigitalSignature -FriendlyName "FlightPath Data Certificate (2025)" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
# $password = ConvertTo-SecureString -String "hangzhou" -Force -AsPlainText
# Export-PfxCertificate -cert "Cert:\CurrentUser\My\7A8C77B758400329ABA0F68BC737734BAB4C715F" -FilePath "c:\dev\flightpath\packaging\assets\FlightPathCert.pfx" -Password $password

#
# sign the exe created by the batch script above. this step isn't needed for an app submission because Microsoft will sign it with their root CA
#
C:\"Program Files (x86)"\"Windows Kits"\10\bin\10.0.26100.0\arm64\signtool sign /f c:\dev\flightpath\packaging\assets\FlightPathCert.pfx /p hangzhou /fd SHA256 C:\dev\flightpath\packaging\dist\FlightPathData.msix

