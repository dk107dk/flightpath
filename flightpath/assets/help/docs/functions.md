## The functions: how to read

The functions documentation is driven from the code. It is rendered both in
FlightPath and in CsvPath Framework's CLI. Each description holds a lot of
information. Some of the details may be different than what you would
expect from a similar domain specific language.


## Sections
There are two main sections:
* A narrative description
* Usage details

Within the Usage section you will see:
* Action type
* Schema type
* Aliases
* Signatures
* Qualifiers


## Usage

### Action type
Every function in CsvPath Language is one of three things:
* A value-producer
* A match-decider
* A side-effect

Each of these `focuses` tells the main goal of the function. A
function may offer capabilities that cross over focuses, but all
have a main goal. Knowing what a function focuses on may help
you, as a csvpath writer, choose the best tool for the job.

#### Value-producers
A value-producer is mainly for producing a calculated value.
Value-producers may contribute to matching, but if they do it is
usally in the form of an existence test on the value they produce.

#### Match-deciders
Match-deciders are primarily focused on producing a boolean `vote`
on if a line should be considered to match the csvpath.

#### Side-effects
Side-effect provide an action that doesn't contribute to the csvpath's
values or matching. The action is valuable to the csvpath writer, but
is typically immaterial to the evaluation of the csvpath. There are
some side-effects that also trigger actions. For example, a print()
statement can also cause a function to be evaluated.

### Schema type
Functions that are schema types may be used with line() to declare
structural schemas that are similar to SQL table definitions. There
are only a handful of schema types:
* string()
* integer()
* decimal()
* boolean()
* date()
* datetime()
* email()
* url()
* blank()
* none()
* wildcard()

A table-like entity describing a person might look like:
```
    line( string(#firstname), string(#lastname), integer(#age) )
```

### Aliases
Unlike most languages CsvPath Language has many function aliases. The purpose is:
* To be forgiving of forgetting function names
* To allow for a more semantically cognizant approach to writing csvpaths

### Signatures
A function signature is a description of how you call the function. It is the name
of a function along with its arguments. Often functions will have multiple distinct
signatures that represent different combinations of allowable arguments.

In the case of CsvPath Language every signature has two forms:
* Data type signatures
* Value signatures

When you write a function into your csvpath you have to think about the arguments.
There are two things to be aware of:
* What is the form of the function in terms of CsvPath Language data sources
* What are the actual values that are acceptable

The former is the source of data and the latter is the value of the data. Sources are:
* Headers
* Variables
* Functions, typically in general, but sometimes specific functions
* Literals, called terms
* References

A function that takes arguments will determine what sources are acceptable. The
signature that describe the acceptable sources is the `by type` signature.

The other type of signature is a `by value` description of the function's inputs. The
data that comes to the function from the sources (actual values from headers, variable,
and so forth) is all typed according to Python. The `by value` signature indicates the
data types that the function expects. Data that does not match the described actual data
types raises a built-in validation error.

Here is an example of this dichotomy. Take a simplistic csvpath that adds numbers:

```
    $[*][ add(1, 3) ]
```

The simplified by-type signature this matches is:

```
    add( Term, Term )
```

And the, again simplified, by-value signature this usage matches is:

```
    add( int, int )
```

The actual signatures that you can see in FlightPath and the CsvPath Framework CLI are:

```
    add( ['Term', 'Variable', 'Header', 'Function', 'Reference'] , ['Term', 'Variable', 'Header', 'Function', 'Reference'] ... )
```

and:

```
    add( ['', 'int', 'float'] , ['', 'int', 'float'] ... )
```

The `...` indicates that more of the same arguments are allowed.

Among other things, these signatures make it clear that a usage like this will trigger a validation error:

```
    $[*][ add("five", 3) ]
```

Clearly `five` is not addable to `3` because it is a string that cannot be automatically
cast to a number. The value `five` fits the by-type signature but fails the by-value signature.

This difference is important because it means that this correct sourcing of data will
be permitted when it is checked at the start of a run. But each time an illegal value like
`five` is seen an error will be raised. If we have an error policy that allows the run to
continue past errors we will, notwithstanding the error on `five`, finish the run.

### Qualifiers
The last section of the function documentation is qualifiers. Qualifiers change the way
Functions work. For example, a line() like:

```
    $[*][ line( string(#firstname), string(#lastname) ) ]
```

Accepts all lines that have two headers called `firstname` and `lastname`. If we modify the
csvpath by adding the `distinct` qualifier to line() we have a significantly different statement.

```
    $[*][ line.distinct( string(#firstname), string(#lastname) ) ]
```

This version requires that there are two headers, firstname and lastname, and that the
combination of firstname and lastname have no duplicates.

Qualifiers are sometimes vital, other times more of a convenience. For example, the above
csvpath could also be written:

```
    $[*][
        line( string(#firstname), string(#lastname) )
        not( has_dups(#firstname, #lastname) )
    ]
```

This alternate way captures the same matches and it runs with essentially the same performance.
However, it is a bit more overhead to read and understand. It also casts the
csvpath validation approach into using declarative rules as well as declarative structure.
There's nothing wrong with mixing structure and rules. But in this simple example you
might choose to use the simpler approach.

Qualifiers come in three flavors that are called out in the function docs:
* Qualifiers that operate during value calculation
* Qualifiers that impact matching
* Functions that use an arbitrary name qualifier to segment data or as a mnemonic.

Qualifiers may fit in either or both of the first two purposes. And you may use as many
qualifiers as gets the job done.








