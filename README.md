# Twitter-Followers-Bokeh-Graph

The code in this repository creates an interactive html-file. With this file you can explore the relationships between Twitter-Accounts based on their shared Followers.

Example:
Using only bandnames from festivals, the bands are clustering by their music-genre. 


The code follows these steps:

1. Scrape the bandnames from the festival-website.

2. Map the bandnames to a Twitter-Account by using a Twitter-Search and selecting the most likely one.

3. Scrape the basic Twitter-Data (Follower-Count, Tweet-Count, ...) for every band using their Twitter-Mainpage.

4. Use the Twitter-API to receive the ids of their Followers.

5. Compute the shared Followers between every node-pair and weighting the edge by the fraction of actually shared to maximal shared Followers.

6. Format the edges and nodes to fit into gephi.

7. Arrange the layout of the graph in gephi and save it as svg-file.

8. Extract the layout-data from the svg-file and use it to create an interactive html-file with bokeh.
