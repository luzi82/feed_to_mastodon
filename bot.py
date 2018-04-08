import common
import argparse
import random
import sys
import feedparser
import time
import os
from mastodon import Mastodon
import re

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    timestamp = int(time.time())
    config = common.read_json(args.filename)
    assert(config is not None)
    data = common.read_json(config['datafile'])

    feed_list = config['feed_list']

    # init data
    if data is None:
        data = {}
    if 'feed_data_dict' not in data:
        data['feed_data_dict'] = {}
    if 'entry_data_dict' not in data:
        data['entry_data_dict'] = {}
    for feed in feed_list:
        feed_id = feed['id']
        if feed_id not in data['feed_data_dict']:
            data['feed_data_dict'][feed_id] = {}
        if 'last_refresh' not in data['feed_data_dict'][feed_id]:
            data['feed_data_dict'][feed_id]['last_refresh'] = 0

    # select feed
    feed_list = config['feed_list']
    random.shuffle(feed_list)
    
    def refresh_filter(feed):
        feed_id = feed['id']
        last_refresh = data['feed_data_dict'][feed_id]['last_refresh']
        if last_refresh <= timestamp - feed['min_refresh_sec']:
            return True
    feed_list = filter(refresh_filter,feed_list)

    feed_list = list(feed_list)
    feed_list = feed_list[:config['operate_feed_count']]

    if len(feed_list) == 0:
        sys.exit(0)

    # output feed data

    try:
        for feed in feed_list:
            feed_id = feed['id']
            max_output_count = feed['max_output_count']
            if 'show_summary' in feed:
                show_summary = (feed['show_summary']!=0)
            else:
                show_summary = True
            
            mm = Mastodon(
                api_base_url = feed['mastodon_account']['api_base_url'],
                client_id = feed['mastodon_account']['client_id'],
                client_secret = feed['mastodon_account']['client_secret'],
                access_token = feed['mastodon_account']['access_token']
            )
    
            data['feed_data_dict'][feed_id]['last_refresh'] = timestamp
    
            fp = feedparser.parse(feed['feed_source']['url'])
            feed_entry_list = list(fp.entries)
            def filter_memory(feed_entry):
                feed_entry_id = feed_entry.id
                entry_data_id = '{0}|{1}'.format(feed_id, feed_entry_id)
                return entry_data_id not in data['entry_data_dict']
            feed_entry_list = filter(filter_memory,feed_entry_list)
            if 'match_regex' in feed['feed_source']:
                def filter_match_regex(feed_entry):
                    pattern = feed['feed_source']['match_regex']
                    title = feed_entry.title
                    return (re.fullmatch(pattern,title) is not None)
                feed_entry_list = filter(filter_match_regex,feed_entry_list)
            feed_entry_list = sorted(feed_entry_list,key=lambda x: (x.published_parsed,x.id))
            feed_entry_list = list(feed_entry_list)
            feed_entry_list = feed_entry_list[:max_output_count]
            for feed_entry in feed_entry_list:
                feed_entry_id = feed_entry.id

                # mark done
                entry_data_id = '{0}|{1}'.format(feed_id, feed_entry_id)
                data['entry_data_dict'][entry_data_id] = {}
                data['entry_data_dict'][entry_data_id]['last_seen'] = timestamp
    
                feed_entry_text = feed_entry.summary
    
                char_limit = config['char_limit']
                char_limit-=len(feed_entry.title)
                char_limit-=len(feed_entry.link)
                feed_entry_text = feed_entry_text[:char_limit]
                
                if show_summary:
                    spoiler_text = feed_entry.title
                    status = '{0}\n\n{1}'.format(feed_entry_text,feed_entry.link)
                    sensitive = True
                else:
                    spoiler_text = None
                    status = '{0}\n\n{1}'.format(feed_entry.title,feed_entry.link)
                    sensitive = False

                if args.test:
                    print(feed_entry.published)
                    print(sensitive)
                    print(spoiler_text)
                    print(status)
                    print('=======================')
                else:
                    mm.status_post(status=status, sensitive=sensitive, spoiler_text=spoiler_text)
    except:
        print(sys.exc_info()[0])

    # forget old entry
    def should_remember(k,v):
        return v['last_seen'] >= timestamp-config['entry_remember_sec']
    data['entry_data_dict'] = {k:v for k,v in data['entry_data_dict'].items() if should_remember(k,v)}

    common.write_json(config['datafile'],data)
