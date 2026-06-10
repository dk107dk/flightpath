## Transfers

This dialog sets state-based transfers at the level of named-paths group configuration.

*It is also possible to use the simpler `transfer-mode:` setting on individual csvpath statements; however, transfer mode doesn't give the flexibility and consolidated view the group-level config does. The two approaches to transfers can be used at the same time without interference. For more information about `transfer-mode` see the modes help content in the right-hand sidebar.*

&nbsp;

### The Action Of Transfers
Transfers move result files to other locations that may be in any of the supported backends. Transfers are grouped according to:
- Csvpath statement
- The end state of the csvpath statement

The run states are the same as for webhooks and scripts:
- All runs
- Valid runs
- Invalid runs
- Runs with errors

Remember that validity is set two ways:
- By the csvpath writer using the `fail()` function
- By built-in validations and `error()` if `validation-mode:` includes the `fail` setting

&nbsp;

### The Parts Of a Transfer
As a configuration action the parts of a transfer are:
- The identity of a csvpath statement
- A result file name or token
- A run variable with its ending value being the path to transfer the file to

Any file can be transferred. The name of the file is the most specific way to indicate what file will be transferred. The standard run output files can also be indicated by their names, minus the file extension:
- data == data.csv
- vars == vars.json
- errors == errors.json
- unmatched == unmatched.json
- meta == meta.json
- printouts == printouts.txt
- manifest == manifest.json

Any other file, primarily printouts text files and parquet files, must be indicated with the full name.

You can transfer any result file as many times as needed. Files can be sent to any backend that is configured, not just the backends used for registered files, statement groups, and the archive. In addition, any SFTP servers configured on the named-paths group can be a transfer destination.


