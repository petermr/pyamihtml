# JEOR_Table project

## Summary of discussion and PMR thoughts with @Jay and @Joshy Alphonse 2024-01-18

on extracting phytochemical profiles from JEOR:
* How do we find the articles that are relevant? we didn't talk about this in detail. May be easiest to search all articles by content
* How to find the relevant table/s. It should have:
  - a title which can be analysed for phrase frequency
  - a column of chemicals .
    o The heading may be "Compound" or similar
    o The contents are normally trivial or systematic names (not structures, not reference numbers)
  - There is often a "GC column/s" labelled "KI" or "RI" . The values are not normally needed
  - There is an abundance/profile column
    o labelled "Relative amount", "avg area" etc.
    o values are floating-point , optionally with ranges
       OR symbols ("tr")
  - 
* In many cases it is "easy" to extract 2 columns, but in others there may be multiple experiments or sources in the same table. These are more difficult.

## How to extract the table (design of results).
much of this is prototyped in CEVOpen
ACTIONS:
@Jay
 to report on :
occurrence of tables in JEOR
how to automatically download - can this be done without subscription
occurrence of EPUB, HTML
overview of the issues above
automation of the process
given that it was ?5 years since 
@Peter Murray-Rust
 write an extractor we can assume that JEOR may have changed and this needs redoing. IF an article has an EPUB (i.e. HTML) then this will be the simplest and very powerful way to analyse it. 
@Peter Murray-Rust
 to read 
@Jay
 report and then discuss strategy with 
@GY
.  If the design is agreed then writing the software shouls be relatively easy.
if so 
@Jay
 and 
@Peter Murray-Rust
 to work together on extraction software