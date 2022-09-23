# Hiking trail matcher
This tool was build to quickly enrich the hiking trails in Wikidata.

It gets a list of hiking trails from Wikidata that are 
missing an OSM relation ID and looks them up in the waymarked trails database.

Then it shows the result to the user and ask them pick the matching one if any.
## Screenshot
![bild](https://user-images.githubusercontent.com/68460690/191992483-079807db-a9b3-4965-a8c0-1ef8f3c03ece.png)

## Operation
First the tool checks via OSM Wikidata Link if there is a single relation in OSM already linking to the item.
If yes the tool presents the match for approval to the user.

If no match is found via OSM Wikidata Link the tool 
proceeds to lookup the label of the route in the Waymarked Trails database. 
If the user cannot decide whether they match, they are provided with links to make further investigatation easier.
If the user choose "no match" then a no-value statement with the current date is uploaded to Wikidata.
If the user accepts a match it is uploaded to Wikidata at once.

## Invocation
### Windows
`$ winpty python.exe app.py`

# License
GPLv3+

# What I learned writing this tool
* first time I used https://github.com/tmbo/questionary and I like it a lot! 
I got it to work in Windows too thanks to a fantastic error message with a hint.
* mypy and typing of everything makes for much higher quality code 
and it is way easier to rewrite because tests and typing in concert 
quickly catches errors before they make it into the repo.
* review and sharing ideas with others is very helpful. multiple minds think better than one.
* it's fun to match!
* I tried keeping all methods small in this project and it was somewhat of a challenge to invent good names for all the methods. 
