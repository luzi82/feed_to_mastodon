# feed_to_mastdon

## setup

1. pip3 install --user --upgrade feedparser mastodon.py beautifulsoup4
1. cp config.json.sample config.json
1. edit config.json
1. test run: python3 bot.py config.json
1. setup crontab: copy and edit res/crond to /etc/cron.d/feed_to_mastodon
