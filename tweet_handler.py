import re
import sys
import json
from pprint import pprint
from twython import exceptions

class bcolors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

class Tweet(object):
  def __init__(self, tweet_dict):
    self.raw = tweet_dict
    self.shown = False

  def __getattr__(self, name):
    return self.raw.get(name, None)

class TweetHandler(object):
  def __init__(self, client):
    self.client = client
    self._init_commands()
    self.tweets = []

  def load_timeline(self):
    sys.stderr.write('Loading timeline...')
    try:
      tweets = self.client.get_home_timeline()
      with open('temp', 'w') as f:
        json.dump(tweets, f)
    except exceptions.TwythonRateLimitError as e:
      #print 'Sorry, too many requests. Please try again later.'
      #import pudb; pu.db
      #print e
      #return
      with open('temp') as f:
        tweets = json.load(f)
    print 'Found %d tweets' % len(tweets)
    self.tweets = [Tweet(tweet) for tweet in tweets]

  def _init_commands(self):
    self.commands = {
      't': self.load_timeline,
      'timeline': self.load_timeline
    }

  def print_tweets(self, max=10):
    for tweet in self.tweets:
      if tweet.shown:
        continue
      self.print_tweet(tweet)

  def print_tweet(self, tweet):
    formatted_text = '\n'.join('  %s' % line for line in tweet.text.split('\n'))
    print '%s%s\n    %s%s%s' % (
      bcolors.PINK, tweet.user['name'],
      bcolors.BLUE, formatted_text, bcolors.ENDC)

  def loop(self):
    self.load_timeline()
    self.print_tweets()
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
