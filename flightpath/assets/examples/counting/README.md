# Counting


These examples show different ways to count lines and data.


There are a number of ways to do similar counts that have separate purposes but
which overlap.  For example:


* increment() adds 1 each N times a match component evaluates to True
* counter() adds N each time a match component evaluates to True
* every() adds 1 every N-times a value is seen, matching or not
  

Likewise, summing offers options:


* sum() keeps a running count of values in a header
* count() keeps a count of matches and, like every(), can also count match
  components it contains
* subtotal() tracks the running sum of a header for each value in another header
* tally() tracks counts of the values seen in headers or combinations of
  headers
  
  
