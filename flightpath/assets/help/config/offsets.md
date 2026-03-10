## Date Offsets

In testing, as well as some unusual situations, you may need FlightPath Data and the CsvPath Framework think it is a different day then it actually is. This form allows you to set the apparent date by the addition or subtraction of days, months, and years.

For example, to make FlightPath Data and CsvPath Framework think it is yesterday, set the days offset to -1.

You must use the buttons on this form to set the offsets. They are intentionally not changed by saving the config as a whole because if you unintentionally set the offsets it is likely to be disruptive.

Note that the offsets only have an effect on the present FlightPath Data session. They do not impact FlightPath Server or any CsvPath Framework activity that is not initiated within FlightPath Data. Offsets are never persisted across sessions. When you close FlightPath Data they are dismissed and must be reset, if desired, when you next open FlightPath Data.

