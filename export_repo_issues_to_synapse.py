"""
This is strongly based on https://gist.github.com/unbracketed/3380407;
thanks to @unbracketed and the various commenters on the page.

I've mainly cleaned up the code into basic methods, and included the
various suggestions in the comments. Hope this is useful to someone.

Make sure you have `requests` and `csv` installed via pip then run it:
`python export_gh_issues_to_csv.py`

---

Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) or token to retrieve Issues
from a repository that username has access to. Supports Github API v3.
"""

import sys
import os
import csv
import logging
import tempfile

import requests
import synapseclient
synapseclient.cache.CACHE_ROOT_DIR = '/tmp/synapsecache/'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
SYNAPSE_USERNAME = os.environ['SYNAPSE_USERNAME']
SYNAPSE_API_KEY = os.environ['SYNAPSE_API_KEY']

# Update your filter here.  See https://developer.github.com/v3/issues/#list-issues-for-a-repository
# arrive in the same results set
# Note that filtering is powerful and there are lots of things available. Also that issues and PRs
params_payload = {'filter' : 'all', 'state' : 'open', 'type': 'issue' }

def write_issues(response, csvout):
    "output a list of issues to csv"
    logger.info("  : Writing %s issues" % len(response.json()))
    for issue in response.json():
        labels = issue['labels']
        label_string = ''
        for label in labels:
            label_string = "%s, %s" % (label_string, label['name'])
        label_string = label_string[2:]

        if issue['milestone']:
            milestone = issue['milestone'].get('title', None)
        else:
            milestone = None

        csvout.writerow([issue['number'], issue['title'].encode('utf-8'),
                         label_string.encode('utf-8'), issue['created_at'],
                         issue['updated_at'], issue['html_url'], milestone])


def get_issues(url):
    kwargs = {
        'headers': {
            'Content-Type': 'application/vnd.github.v3.raw+json',
            'User-Agent': 'GitHub issue exporter'
        },
        'params': params_payload
    }
    if GITHUB_TOKEN != '':
        kwargs['headers']['Authorization'] = 'token %s' % GITHUB_TOKEN
    else:
        kwargs['auth'] = (GITHUB_USER, GITHUB_PASSWORD)

    logger.info("GET %s" % url)
    resp = requests.get(url, **kwargs)
    logger.info("  : => %s" % resp.status_code)

    # import ipdb; ipdb.set_trace()
    if resp.status_code != 200:
        raise Exception(resp.status_code)

    return resp


def next_page(response):
    #more pages? examine the 'link' header returned
    if 'link' in response.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
                [link.split(';') for link in
                    response.headers['link'].split(',')]])
        # import ipdb; ipdb.set_trace()
        if 'last' in pages and 'next' in pages:
            return pages['next']

    return None

def process(csvout, url):
    resp = get_issues(url)
    write_issues(resp, csvout)
    next_ = next_page(resp)
    if next_ is not None:
        process(csvout, next_)

def delete_all_rows(syn, table_id):
    q = syn.tableQuery('select id from %s' % (table_id, ))
    return syn.delete(q.asRowSet())

def issues_to_table_handler(event, context):

    table_id = event['table_id']

    repo = event['repo']
    issues_url = 'https://api.github.com/repos/%s/issues' % repo

    syn = synapseclient.login(email=SYNAPSE_USERNAME,
                              apiKey=SYNAPSE_API_KEY,
                              silent=True)

    tmpfile = tempfile.NamedTemporaryFile(suffix=".csv")
    csvout = csv.writer(tmpfile)
    csvout.writerow(('id', 'Title', 'Labels', 'Created At', 'Updated At', 'URL', 'Milestone'))
    process(csvout, url=issues_url)
    tmpfile.flush()

    logger.debug("Wrote to %s" % tmpfile.name)

    try:
        a = delete_all_rows(syn, table_id)
    except synapseclient.exceptions.SynapseHTTPError:
        pass

    table = syn.store(synapseclient.Table(syn.get(table_id),
                                          tmpfile.name))

    return {'message': "Stored issues to table %s" % (table_id, )}

def main():

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--table_id", type=str)
    parser.add_argument("repo", type=str)

    args = parser.parse_args()

    event = {"table_id": args.table_id, "repo": args.repo}

    message = issues_to_table_handler(event=event, context=None)

    logger.info(message)

if __name__ == "__main__":
    main()
