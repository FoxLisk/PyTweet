from twython import Twython
import settings
import sys
try:
  import user_settings
  do_setup = True
except ImportError:
  do_setup = False

def setup():
  twitter = Twython(
      settings.APP_KEY,
      settings.APP_SECRET)
  auth = twitter.get_authentication_tokens(callback_url='oob')
  oauth_token = auth['oauth_token']
  oauth_secret = auth['oauth_token_secret']

  twitter2 = Twython(settings.APP_KEY, settings.APP_SECRET,
                    oauth_token, oauth_secret)

  pin = raw_input('Please visit the following site, click accept, and '
      'enter the pin number provided\n  %s\n' % auth['auth_url'])

  try:
    final_step = twitter2.get_authorized_tokens(pin)
  except Exception as e:
    print 'Error authenticating, please try again'
    import pudb; pu.db
    return False
  
  with open('user_settings.py', 'w') as f:
    f.write('oauth_token="%s"\n' % final_step['oauth_token'])
    f.write('oauth_token_secret="%s"' % final_step['oauth_token_secret'])
  return True

if not do_setup:
  if not setup():
    sys.exit(1)
  import user_settings

twitter = Twython(settings.APP_KEY, settings.APP_SECRET,
                  user_settings.oauth_token, user_settings.oauth_token_secret)

tweets = twitter.get_home_timeline()
