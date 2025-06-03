# Deploying csvpaths in a named-paths group


This example loads three csvpath files from the first steps directory into two named-paths groups. 

### What is a named-paths group?

A named-paths group is a set of csvpaths that are run as a unit. Each run has a single data input. Every csvpath in the named-paths group run has its own separate results.

### Why do I need named-paths groups?

Creating a simple csvpath is easy. But when a you need to enforce dozens or hundreds of rules one csvpath becomes limiting and complicated. Complex rule sets should be broken down into multiple simple csvpaths for easier development and testing. Then once you're ready, the simple csvpaths can be easily aggregated into a named-paths group and run together. 

### What is this JSON file?

The JSON file is a definition for the named-paths groups. You can create named-paths groups in multiple ways. Defining them in JSON adds a step -- creating the JSON file -- but gives you the most control.

### How do I run the example?

Right-click on the JSON file and select **Load csvpaths**.  A one-option dialog opens. When you click the create or overwrite button you'll see your csvpaths loaded in the **Csvpath groups** window on the right-hand side of FlightPath. It's pretty much that simple.

