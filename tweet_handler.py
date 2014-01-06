import re
import sys
import json
from pprint import pprint
from twython.exceptions import TwythonRateLimitError
from datetime import datetime

DATETIME_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'

class bcolors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

class Tweet(object):
  id_ctr = 0
  def __init__(self, tweet_dict):
    self.raw = tweet_dict
    self.shown = False
    self.is_rt = 'retweeted_status' in tweet_dict
    self._id = Tweet.id_ctr
    Tweet.id_ctr += 1

  def __getattr__(self, name):
    return self.raw.get(name, None)

  def _format_normal(self):
    formatted_text = '\n'.join('  %s' % line for line in self.text.split('\n'))
    return '%s%s %s\n%s%s%s' % (
      bcolors.PINK, self.user['name'], self.created_at,
      bcolors.BLUE, formatted_text, bcolors.ENDC)

  def _format_rt(self):
    formatted_text = '\n'.join('  %s' % line for line in
      self.retweeted_status['text'].split('\n'))
    header = '%s%s %s %s(RTd by %s)' % (
      bcolors.PINK, self.retweeted_status['user']['name'],
      bcolors.GREEN, self.user['name'], self.created_at)
    return '%s\n%s%s%s' % (header, bcolors.BLUE, formatted_text, bcolors.ENDC)

  def format(self):
    if self.is_rt:
      return self._format_rt()
    else:
      return self._format_normal()
    
class TweetHandler(object):
  def __init__(self, client):
    self.client = client
    self.tweets = []
    self.seen_ids = set([])
    self.largest_id = None
    self._init_commands()

  def _fetch_tweets(self):
    try:
      tweets = self.client.get_home_timeline(since_id=self.largest_id)
      tweets = sorted(tweets, None,
                      lambda t: datetime.strptime(t['created_at'], DATETIME_FORMAT))
      with open('temp', 'w') as f:
        json.dump(tweets, f)
      return tweets
    except TwythonRateLimitError as e:
      print 'Sorry, too many requests. Please try again later.'
      if not self.tweets:
        with open('temp') as f:
          tweets = json.load(f)
        return tweets
      else:
        return []

  def load_timeline(self):
    sys.stderr.write('Loading timeline...')
    tweets = self._fetch_tweets()
    print 'Found %d tweets' % len(tweets)
    if tweets:
      self.largest_id = tweets[-1]['id_str']
      self.tweets.extend({Tweet(tweet) for tweet in
                         reversed(tweets) if tweet['id_str'] not in self.seen_ids})
      self.seen_ids.update([tweet['id_str'] for tweet in tweets])
    self.print_tweets()

  def _init_commands(self):
    self.commands = {
      't': self.load_timeline,
      'timeline': self.load_timeline
    }

  def print_tweets(self, max=10):
    for tweet in self.tweets:
      if tweet.shown:
        print 'Tweet id %s already shown' % tweet.id_str
        continue
      print tweet.format()

  def loop(self):
    self.load_timeline()
    while True:
      user_cmd = raw_input('\n')
      if not user_cmd:
        continue
      if user_cmd == 'q':
        break

      cmd_parts = re.split(r'\s+', user_cmd)
      cmd_name = cmd_parts.pop(0)
      if cmd_name in self.commands:
        self.commands[cmd_name](*cmd_parts)
