from yaml import safe_load as load
import requests
import subprocess
import os
import shutil
import time
import datetime
import sys

REPO_API = 'https://api.github.com/repos/{}'
NOTIFICATIONS_API = 'https://api.github.com/notifications'
TOKEN = os.environ.get('HENCHBOT_TOKEN')


class henchBotRefreeze:
    '''
    Class for a bot that listens for a refreeze request in repo2docker
    '''
    def __init__(self):
        pass

    def check_to_refreeze(self):
        res = requests.get(NOTIFICATIONS_API + '?participating=true', 
                           headers={'Authorization': 'token {}'.format(TOKEN)}).json()
        if res:
            for mention in res:
                is_pr = bool(mention['subject']['type'] == 'PullRequest')
                self.origin_repo = mention['repository']['full_name']
                if mention['subject']['latest_comment_url']:
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

    def refreeze_deps(self, mention):
        pr_info = self.get_pr_info(mention)
        self.clone_and_checkout_branch(pr_info)
        self.run_refreeze_commands()
        self.add_commit_push(pr_info)
        os.chdir('..')
        shutil.rmtree(pr_info['head']['repo']['name'])
        self.comment_on_pr(pr_info)

    def comment_on_pr(self, pr_info):
    	body_text = '''I changed some stuff you're welcome.'''
    	body = {'body': body_text}
    	requests.post(REPO_API.format(self.origin_repo) + '/issues/' + str(pr_info['number']) + '/comments',
    		          headers={'Authorization': 'token {}'.format(TOKEN)}, json=body)

    def get_pr_info(self, mention):
        res = requests.get(mention['subject']['url']).json()
        return res

    def clone_and_checkout_branch(self, pr_info):
        subprocess.check_output(['git', 'clone', pr_info['head']['repo']['html_url']])
        os.chdir(pr_info['head']['repo']['name'])
        subprocess.check_output(['git', 'fetch', 'origin', pr_info['head']['ref']])
        subprocess.check_output(['git', 'checkout', pr_info['head']['ref']])

    def add_commit_push(self, pr_info):
        subprocess.check_output(['git', 'add', '-A'])
        subprocess.check_call(['git', 'config', 'user.name', 'henchbot'])
        subprocess.check_call(['git', 'config', 'user.email', 'henchbot.github@gmail.com'])
        subprocess.check_output(['git', 'commit', '-m', 'conda buildpack refreeze'])
        subprocess.check_output(['git', 'push', 'origin', pr_info['head']['ref']])

    def run_refreeze_commands(self):
        os.chdir('repo2docker/buildpacks/conda')
        subprocess.check_output(['./freeze.py'])
        os.chdir('../../..')


if __name__ == '__main__':
    hb = henchBotRefreeze()
    hb.check_to_refreeze()
