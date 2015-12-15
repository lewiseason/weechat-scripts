"""
pushover.py: send pushover notifications when mentioned or messaged.

---

Author:  Lewis Eason <me@lewiseason.co.uk>
License: WTFPL <http://www.wtfpl.net/>

---

TODO:
  * Toggle "away" detection
"""

import weechat
import urllib, json

VERSION = '1.2'
DESCRIPTION = __doc__.split('---', 1)[0].strip()

OPTIONS = {
    'userkey':  ('', 'User key for pushover.net (required)'),
    'apptoken': ('', 'App token for pushover.net (required)'),
    'sound':    ('default', 'Sound to request pushover use'),
    'timeout':  ('5000', 'How long to wait for pushover to accept a message', int),
}

def init_options():
    global OPTIONS
    notransform = lambda x: x

    for option, value in list(OPTIONS.items()):
        weechat.config_set_desc_plugin(option, '%s (default: "%s")' % (value[1], value[0]))

        if not weechat.config_is_set_plugin(option):
            weechat.prnt('', 'x')
            weechat.config_set_plugin(option, value[0])

        if len(value) > 2:
            transform = value[2]
        else:
            transform = notransform

        OPTIONS[option] = transform(weechat.config_get_plugin(option))

def message_sent(data, command, rc, out, err):
    result = json.loads(out)

    if rc == 0 and result.get('status') == 1:
        return weechat.WEECHAT_RC_OK

    weechat.prnt('', 'pushover: Failed to send the message (Request: {})'.format(result['request']))
    return weechat.WEECHAT_RC_ERROR

def notify(data, buffer, timestamp, tags, displayed, highlighted, prefix, message):
    buffer_name = weechat.buffer_get_string(buffer, 'name')
    buffer_type = weechat.buffer_get_string(buffer, 'localvar_type')
    server      = weechat.buffer_get_string(buffer, 'localvar_server')

    message     = None

    if buffer_type not in ['private', 'channel']:
        return weechat.WEECHAT_RC_OK

    if buffer_type == 'channel' and highlighted == 0:
        return weechat.WEECHAT_RC_OK

    if buffer_type == 'private':
        message = '{nick} sent you a private message on {server}'.format(nick=prefix, server=server)

    elif buffer_type == 'channel':
        channel = buffer_name.split('.', 1)[1]
        message = '{nick} mentioned you in {channel}'.format(nick=prefix, channel=channel)

    if message == None:
        return weechat.WEECHAT_RC_OK

    process_endpoint = 'url:https://api.pushover.net:443/1/messages.json'
    post_data = urllib.urlencode({
        'token':   OPTIONS['apptoken'],
        'user':    OPTIONS['userkey'],
        'sound':   OPTIONS['sound'],
        'message': message,
    })

    weechat.hook_process_hashtable(process_endpoint, { 'post': '1', 'postfields': post_data }, OPTIONS['timeout'], 'message_sent', '')

    return weechat.WEECHAT_RC_OK

if __name__ == '__main__':
    weechat.register('pushover', 'Lewis Eason <me@lewiseason.co.uk>', VERSION, 'WTFPL', DESCRIPTION, '', '')
    weechat.hook_print('', 'irc_privmsg,notify_msg', '', 1, 'notify', '')
    init_options()

