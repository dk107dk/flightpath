## Errors

This config section determines the channels and format for how CsvPath displays error messages. Logging is just one important channel for errors, as well as other information. It has its own configuration section.

Setting the error handling configuration options impacts all csvpaths in all runs. You can also override these configuration file settings for any given csvpath using a mode setting within an external comment. (External comments come above the csvpath). The mode is <i>validation-mode</i>. You would use validation mode like:

```
    ~ validation-mode: print, stop, collect ~
    $[*][ add("five", 5) ]
```
This csvpath will print an error message because <i>"five"</i> is not an integer and cannot be added.

CsvPath Framework generates three types of errors:
- Validation errors - problems with your data
- CsvPath Language errors - problems with how you wrote the csvpaths you are using to validate and upgrade your data
- Other configuration and system errors - problems with your use of CsvPath Framework or internal problems in CsvPath Framework code

The errors configuration is super important because it determines how communicative the Framework is. You can essentially turn off error reporting. When you do that you deprive yourself of information and may confuse not seeing errors with there not being any errors. Likewise, if you turn error handling up to 11, requiring the Framework to raise exceptions for all errors, you will halt processing in ways that might be detrimental in a production context.

There are several error reporting channels and options.
<table border='1' cellspacing='0' cellpadding='2' style='border:1px solid #333;margin-top:10px'>
<tr>
    <td style='background-color:#333;color:#fff'>Channel/option</td>
    <td style='background-color:#333;color:#fff'>Token</td>
    <td style='background-color:#333;color:#fff'>Purpose</td>
</tr>
<tr>
    <td>Logging</td>
    <td><i>log</i></td>
    <td>Logging has four levels: <i>DEBUG</i>, <i>INFO</i>, <i>WARN</i>, and <i>ERROR</i>, in decreasing order of volume. <i>INFO</i> and <i>DEBUG</i> include non-error information that may be useful but can be overwhelming. If you are having trouble getting the results you need cranking up logging can help.</td>
</tr>
<tr>
    <td>Printing</td>
    <td><i>print</i></td>
    <td>This is the most useful option, for most purposes. Print simply prints out the error messages in a customizable format with minimal effect on the run in progress.</td>
</tr>
<tr>
    <td>Error collection</td>
    <td><i>collect</i></td>
    <td>When collection is turned on errors are collected to the error tab, for ad hoc runs, or the <i>errors.json</i> result file for named-paths group runs.</td>
</tr>
<tr>
    <td>Raising exceptions</td>
    <td><i>raise</i></td>
    <td>Raising exceptions stops processing on the first error. You will see a stack trace in the log. Raising an exception gives you lots of information, particularly about Framework internals. But you may not get all the information you require for triage because the Framework isn't attempting to communicate its internal state and deliberations, it is only blowing up. It may be helpful to first print and increase logging, before raising an exception.</td>
</tr>
<tr>
    <td>Stopping processing</td>
    <td><i>stop</i></td>
    <td>Stop halts the run at the line where the error occurred. The current line is not guaranteed to complete its evaluation.</td>
</tr>
<tr>
    <td>Marking a run failed </td>
    <td><i>fail</i></td>
    <td>This option shows up in runtime and results metadata. It simply marks the run as failed, without taking any other steps to affect the run or communicate with the user.</td>
</tr>
</table>


