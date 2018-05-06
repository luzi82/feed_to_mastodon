#!/bin/bash

pip3 install --user --upgrade feedparser mastodon.py beautifulsoup4
sudo cp res/crond /etc/cron.d/feed_to_mastodon
