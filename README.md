
Simple RSS reader.

# Features #
* All articles links are presented in a single html page
* Articles are read on the original website
* A script is provided to run it with a Bottle http server
* Threads are used to speed-up feeds reading
* Feeds are stored in a temporary file to reduce bandwidth when re-reading feeds

# Non-features #
* Read / unread for articles. Visited links color is enough for that
* Articles saving. Nothing is saved, except a temporary file to avoid re-downloading a feed with no modifications

# Files #
* `feeds.json` : contains the list of feeds to download
* `rssread.py` : create an index.html page containing the list of article for last week
* `start_server.py` : bottle script to run an http server on port 8080. a GET on this address will run rssread.py and return the generated index.html
* `rssread.service` : systemd service file to start bottle http server on computer startup. To be copied in /etc/systemd/system/

