#!/usr/bin/python3

import json
import sqlite3


class Feed:
    def __init__(self, url, img_url=None):
        self.url = url
        self.img_url = img_url


def main():
    with open("feeds.json", "r") as f:
        feeds = read_feeds_list(f)
    with sqlite3.connect("rssread.db") as db_connection:
        save_feeds(feeds, db_connection)


def read_feeds_list(file_handle):
    parsed_feeds = json.load(file_handle)
    feeds = []
    for feed in parsed_feeds:
        feeds.append(Feed(feed["url"], feed.get("img", None)))
    return feeds


def save_feeds(feeds, db_connection):
    db_connection.execute('CREATE TABLE IF NOT EXISTS feeds (feed_id INTEGER PRIMARY KEY, url TEXT UNIQUE, img_url TEXT, active INTEGER)')
    db_connection.execute('UPDATE feeds SET active=0')
    for feed in feeds:
        db_connection.execute('UPDATE feeds SET img_url=?, active=1 WHERE url=?', (feed.img_url, feed.url))
        db_connection.execute('INSERT OR IGNORE INTO feeds(url, img_url, active) VALUES (?, ?, 1)', (feed.url, feed.img_url))
    db_connection.execute('DELETE FROM feeds WHERE active=0')
    db_connection.commit()


if __name__ == "__main__":
    main()

