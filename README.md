# Hiking trail scraper
This tool was build to quickly enrich the hiking trails in Wikidata.

It gets a list of hiking trails from Wikidata that are 
missing an OSM relation ID and looks them up in the waymarked trails database.

Then it shows the result to the user and ask them pick the matching one if any.
## Screenshot
![bild](https://user-images.githubusercontent.com/68460690/191992483-079807db-a9b3-4965-a8c0-1ef8f3c03ece.png)

## Invocation
### Windows
`$ winpty python.exe app.py`
