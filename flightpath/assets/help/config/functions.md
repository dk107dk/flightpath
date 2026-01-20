## Custom Functions

This panel is for pointing to a file that defines custom functions. Custom functions are CsvPath Validation Language functions written in Python by the end user. Their purpose is to allow for:
* Adding new functionality
* Overriding the existing functions with new code

Custom functions are loaded on a project by project basis. They will never conflict across projects or provide unintended capabilities to other projects.

Position your custom functions under the config folder of your project. The functions are loaded based on a configuration file usually called `functions.imports`. The imports file has a line for each function in the same form as a Python import statement. E.g.
```
    from a.b.c import C as my_function
```

You can then use your custom function as you would any other function. For example:
```
    $[*][ my_function() ]
```

There is no limit on the number of custom functions. You will not get a warning if you override a built-in function.



