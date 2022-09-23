# Hiking trail scraper
This tool was build to quickly enrich the hiking trails in Wikidata.

It gets a list of hiking trails from Wikidata that are 
missing an OSM relation ID and looks them up in the waymarked trails database.

Then it shows the result to the user and ask them pick the matching one if any.
## Screenshot
![bild](https://user-images.githubusercontent.com/68460690/191992483-079807db-a9b3-4965-a8c0-1ef8f3c03ece.png)

## Operation
If the user cannot decide whether they match, they are provided with links to make further investigatation easier.
If the user choose "no match" then a no-value statement with the current date is uploaded to Wikidata.
If the user accepts a match it is uploaded to Wikidata at once.

## Invocation
### Windows
`$ winpty python.exe app.py`
