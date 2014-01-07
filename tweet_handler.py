import re
import sys
import json
from pprint import pprint, pformat
from twython.exceptions import TwythonRateLimitError
from datetime import datetime

DATETIME_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'

class bcolors:
    MAGENTA = '\033[35m'
    BLUE    = '\033[34m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    RED     = '\033[31m'
    ENDC    = '\033[0m'
    BLACK   = "\033[30m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

class Tweet(object):
  id_ctr = 0
  HEADER_FORMAT = u'{cun}{username} {csn}(@{screen_name}){crt}{rt_string} {cdate}{date} {cid}{id}{cend}'
  FORMAT_COLORS = {
    'cun': bcolors.MAGENTA,
    'csn': bcolors.MAGENTA,
    'crt': bcolors.CYAN,
    'cdate': bcolors.BLUE,
    'ctext': bcolors.WHITE,
    'cend': bcolors.ENDC,
    'cid': bcolors.WHITE
  }

  def __init__(self, tweet_dict):
    self.raw = tweet_dict
    self.shown = False
    self.is_rt = 'retweeted_status' in tweet_dict
    self._id = Tweet.id_ctr
    Tweet.id_ctr += 1
    self.date = datetime.strptime(tweet_dict['created_at'], DATETIME_FORMAT)
    if self.is_rt:
        self.date = datetime.strptime(tweet_dict['retweeted_status']['created_at'], DATETIME_FORMAT)

  def get_authors(self):
    authors = [self.user['screen_name']]
    if self.is_rt:
      authors.append(self.retweeted_status['user']['screen_name'])
    props = self.raw
    if self.is_rt:
      props = self.retweeted_status
    authors.extend(user['screen_name'] for user in props['entities']['user_mentions'])
    return ['@%s' % author for author in authors]

  def __getattr__(self, name):
    return self.raw.get(name, None)

  def _format_header(self):
    options = {
      'pink': bcolors.MAGENTA,
      'username': self.user['name'],
      'screen_name': self.user['screen_name'],
      'date': self.date.strftime('%d/%m/%y %H:%M'),
      'rt_string': '',
      'id': self._id
    }
    options.update(self.FORMAT_COLORS)

    if self.is_rt:
      options['rt_string'] = ' (RTd by %s)' % self.user['name']
      options['screen_name'] = self.retweeted_status['user']['screen_name']
      options['username'] = self.retweeted_status['user']['name']
    return self.HEADER_FORMAT.format(**options)

  def _format_normal(self):
    formatted_text = '\n'.join('  %s' % line for line in self.text.split('\n'))
    options = {'text': formatted_text, 'header': self._format_header()}
    options.update(self.FORMAT_COLORS)
    return u'{header}\n{ctext}{text}{cend}'.format(**options)
      

  def _format_rt(self):
    formatted_text = '\n'.join('  %s' % line for line in
      self.retweeted_status['text'].split('\n'))
    options = {'text': formatted_text, 'header': self._format_header()}
    options.update(self.FORMAT_COLORS)
    return u'{header}\n{ctext}{text}{cend}'.format(**options)

  def format(self):
    if self.is_rt:
      return self._format_rt()
    else:
      return self._format_normal()
    
class TweetHandler(object):
  def __init__(self, client):
    self.client = client
    self.tweets = []
    self.largest_id = None
    self._init_commands()
    self.tweet_dict = {}

  def _fetch_tweets(self):
    try:
      tweets = self.client.get_home_timeline(since_id=self.largest_id)
      tweets = sorted(tweets, None,
                      lambda t: datetime.strptime(t['created_at'], DATETIME_FORMAT))
      with open('pretty', 'w') as f:
        f.write(pformat(tweets))
      return tweets
    except TwythonRateLimitError as e:
      print 'Sorry, too many requests. Please try again later.'
      return []

  def add_new_tweets(self, tweets):
    self.largest_id = max(t['id'] for t in tweets)
    o_tweets = [Tweet(tweet) for tweet in tweets]
    self.tweets.extend(o_tweets)
    self.tweet_dict.update({tweet._id: tweet for tweet in o_tweets})

  def load_timeline(self):
    sys.stderr.write('Loading timeline...')
    tweets = self._fetch_tweets()
    print 'Found %d tweets' % len(tweets)
    if tweets:
      self.add_new_tweets(tweets)
    self.print_tweets()

  def _init_commands(self):
    self.commands = {
      's': self.load_timeline,
      'show': self.load_timeline,
      't': self.tweet,
      'tweet': self.tweet,
      'r': self.reply,
      'reply': self.reply
    }

  def tweet(self, text=None):
    if text is None:
      print 'Please enter text to tweet'
      return
    if len(text) > 140:
      print 'Tweet is too long (%d characters total)' % len(text)
      return
    self.client.update_status(status=text)
    print 'Posted "%s" to your account' % text

  def reply(self, reply_to, text=None):
    reply_to = int(reply_to)
    if reply_to not in self.tweet_dict:
      print 'No tweet available with id %d' % reply_to
    reply_tweet = self.tweet_dict[reply_to]
    authors = reply_tweet.get_authors()
    print authors

  def print_tweets(self, max=10):
    for tweet in self.tweets:
      if tweet.shown:
        continue
      print tweet.format()
      tweet.shown = True

  def loop(self):
    self.load_timeline()
    while True:
      user_cmd = raw_input('\n')
      if not user_cmd:
        continue
      if user_cmd == 'q':
        break

      cmd = re.split(r'\s+', user_cmd, maxsplit=1)
      cmd_name = cmd.pop(0)
      if cmd_name in self.commands:
        self.commands[cmd_name](*cmd)
