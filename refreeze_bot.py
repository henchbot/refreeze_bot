from yaml import safe_load as load
import requests
import subprocess
import os
import shutil
import time
import datetime

REPO_API = 'https://api.github.com/repos/henchbot/refreeze_bot/notifications'
NOTIFICATIONS_API = 'https://api.github.com/notifications'
TOKEN = os.environ.get('HENCHBOT_TOKEN')


class henchBotRefreeze:
    '''
    Class for a bot that listens for a refreeze request repo2docker
    '''
    def __init__(self):
        pass

    def check_to_refreeze(self):
        res = requests.get(NOTIFICATIONS_API + '?participating=true', 
                           headers={'Authorization': 'token {}'.format(TOKEN)}).json()
        if res:
            for mention in res:
                is_pr = bool(mention['subject']['type'] == 'Pull Request')
                if is_pr and self.asked_for_refreeze(mention['subject']['latest_comment_url']):
                    self.refreeze_deps(mention)
            	self.mark_as_read(mention['id']) 

    def asked_for_refreeze(self, comment_url):
        res = requests.get(comment_url).json()
        return bool('refreeze' in res['body'])

    def mark_as_read(self, thread_id):
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        requests.patch(NOTIFICATIONS_API + '/threads/{}'.format(thread_id), 
                     params={'last_read_at': now}, 
                     headers={'Authorization': 'token {}'.format(TOKEN)})

    def refreeze_deps(self):
        pass


if __name__ == '__main__':
    hb = henchBotRefreeze()
    hb.check_to_refreeze()
