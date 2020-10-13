import argparse
import configparser
import datetime
import logging
import logging.handlers
import time

import pandas as pd
import requests
from tqdm import tqdm

# --- Absolute Import Fix --- #
# Use this if script needs to be run standalone
import os
import sys
from dotenv import find_dotenv
sys.path.append(os.path.dirname(find_dotenv()))

from textron.util.helpers import function_timer
from textron.util import databases
from textron import CONFIG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s:%(name)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
file_handler = logging.handlers.RotatingFileHandler(filename=CONFIG.LOGS_DIR / 'scraper.log',
                                                    maxBytes=10_000_000, backupCount=10)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'accept-encoding': 'gzip, deflate, sdch, br',
           'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
           'cache-control': 'max-age=0',
           'upgrade-insecure-requests': '1',
           'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}


class RedditScraper:
    """Scrapes one or many subreddits, with or without comments

    Use config files in this directory to configure scraper options rather
    than set them explicitely.
    Documentation of the options is in the config files.

    Parameters
    ----------
    sorting : string, default='new'
        Reddit sort order for posts
        Options: 'new', 'rising', 'controversial', 'top'

    include_comments : bool, default=True
        Whether to include comments for each post

    save_method: string, default='sqlite'
        Save location (and method)

    Returns
    -------
    params : mapping of string to any
        Parameter names mapped to their values.
    """

    def __init__(self, project_name=None, sorting='new', 
                 include_comments=True, save_method='sqlite'):
        self.project_name = project_name
        self.sorting = sorting
        self.include_comments = include_comments
        self.save_method = save_method
        self.date = str(datetime.datetime.now().date())

    def get_post_urls(self, sub_url):
        """Get post URLs for a given subreddit

        Parameters
        ----------
        sub_url : string
            Sub

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        after = None
        posts_url_list = []
        for _ in range(1):
            if after is None:
                params = {}
            else:
                params = {'after': after}
            try:
                response = requests.get(
                    sub_url, params=params, headers=headers, timeout=None)
            except(ConnectionError, ConnectionResetError) as e:
                logger.exception(f'Error scraping {sub_url}: {e}')
                continue
            if response.status_code != 200:
                logger.info(f'Error: {response.status_code}')
                continue

            post_json = response.json()
            post_urls = []
            for post in post_json['data']['children']:
                perma = post['data']['permalink']
                post_url = f'https://www.reddit.com{perma}'
                if post_url not in post_urls:
                    post_urls.append(post_url)
            posts_url_list.extend(post_urls)
            after = post_json['data']['after']
            time.sleep(.1)
        return posts_url_list

    def jsonify_url(self, url):
        url = f'{url[:-1]}.json'
        return url

    def get_post(self, post_json):
        '''Get post info for current url'''
        post_id = post_json[0]['data']['children'][0]['data']['id']
        post_title = post_json[0]['data']['children'][0]['data']['title']
        post_body = post_json[0]['data']['children'][0]['data']['selftext']
        upvotes = post_json[0]['data']['children'][0]['data']['ups']
        return (post_id, post_title, post_body, upvotes)

    def get_comments(self, parent, comments):
        '''Get comments for current url'''
        if comments is None:
            comments = []
        for comment in parent['data']['children']:
            comment_id = comment['data'].get('id')
            comment_body = comment['data'].get('body')
            upvotes = comment['data'].get('ups')
            comments.append((comment_id, comment_body, upvotes))
            replies = comment['data'].get('replies')
            if replies:
                self.get_comments(replies, comments)
        return comments

    def scrape_subreddit(self, subreddit):
        """Scrapes a subreddit for post titles.

        Parameters
        ----------
        subreddit: subreddit to scrape

        Returns
        -------
        (posts_df, comments_df)
        """
        # create URL from subreddit name
        sub_url = f'https://reddit.com/r/{subreddit}/{self.sorting}.json'
        # get list of post URLs
        posts_url_list = self.get_post_urls(sub_url)

        posts_df = pd.DataFrame()
        comments_df = pd.DataFrame()
        for post_url in posts_url_list:
            post_url = self.jsonify_url(post_url)
            try:
                response = requests.get(
                    post_url, params=None, headers=headers, timeout=None)
            except(ConnectionError, ConnectionResetError) as e:
                logger.exception(f'Connection error scraping {sub_url}: {e}')
                continue
            except Exception as e:
                logger.exception('Scraper Exception:', e)
                logger.exception(f'Skipping this post: {sub_url}')
                continue
            if response.status_code != 200:
                logger.info(f'Response Error: {response.status_code}')
                continue
            post_json = response.json()
            post_id, post_title, post_body, upvotes = self.get_post(post_json)
            post_data = pd.DataFrame.from_records(
                [{'post_id': post_id,
                  'post_title': post_title,
                  'post_body': post_body,
                  'upvotes': upvotes,
                  'subreddit': subreddit,
                  'date': self.date
                  }])
            posts_df = pd.concat([posts_df, post_data], ignore_index=True)

            if self.include_comments:
                comments = self.get_comments(parent=post_json[1], comments=None)
                comments_data = pd.DataFrame.from_records(
                    [{'comment_id': comment[0],
                      'post_id': post_id,
                      'comment': comment[1],
                      'upvotes': comment[2]} for comment in comments])
                comments_df = pd.concat(
                    [comments_df, comments_data], ignore_index=True)

        logger.info(f'{len(posts_df)} scraped for "{subreddit}"')
        if self.include_comments:
            return (posts_df, comments_df)
        return (posts_df, None)

    def save_to_csv(self, df, table_name, subreddit):
        save_dir = CONFIG.SCRAPED_DIR / self.project_name
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        df.to_csv(f'{save_dir}/{self.date}_{subreddit}_{table_name}.csv', index=False)

    def save_to_sqlite(self, df, table_name, subreddit):
        db = databases.Sqlite()
        connection = db.create_connection(
            f'{CONFIG.DATABASE_DIR}/{self.project_name}.sqlite')
        cursor = connection.cursor()

        if table_name == 'posts':
            create_posts_table = """
            CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            post_title TEXT NOT NULL,
            post_body TEXT NOT NULL,
            upvotes INTEGER NOT NULL,
            subreddit TEXT NOT NULL,
            date TEXT NOT NULL
            );
            """
            cursor.execute(create_posts_table)

            for row in df.itertuples():
                row_values = [row.post_id, row.post_title, row.post_body, row.upvotes, row.subreddit, row.date]
                cursor.execute('''INSERT or REPLACE into posts (post_id, post_title, post_body, upvotes, subreddit, date) 
                    values (?, ?, ?, ?, ?, ?)''', row_values)
            
            connection.commit()

        if table_name == 'comments':
            create_comments_table = """
            CREATE TABLE IF NOT EXISTS comments (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            comment TEXT NOT NULL,
            upvotes INTEGER NOT NULL
            );
            """
            cursor.execute(create_comments_table)

            for row in df.itertuples():
                row_values = [row.comment_id, row.post_id, row.comment, row.upvotes]
                cursor.execute('''INSERT or REPLACE into comments (comment_id, post_id, comment, upvotes) 
                values (?, ?, ?, ?)''', row_values)

        print('Data saved to sqlite database successfully')
        connection.close()

    def save_to_postgres(self, df, table_name):
        return 'save to postgres'
        # YEAH

    def save_to_mongo(self, df, table_name):
        return 'save to mongo'
        # definitely a FUTURE addition

    def save_to_mysql(self, df, table_name):
        return 'save to mysql'
        # for django or something

    def save_choice(self, df, choice, table_name, subreddit):
        '''
        Choice to save the scraped dataframe.
        Choices:
        'csv', 'sqlite', 'postgres', 'mongo', 'mysql'
        '''
        save_options = {
            'csv': self.save_to_csv,
            'sqlite': self.save_to_sqlite,
            'postgres': self.save_to_postgres,
            'mongo': self.save_to_mongo,
            'mysql': self.save_to_mysql
        }
        save_function = save_options.get(choice, self.save_to_csv)
        return save_function(df, table_name, subreddit)

@function_timer
def main():
    logger.info('PROGRAM STARTED')
    scraper = RedditScraper(project_name=project_name, sorting=sorting, include_comments=include_comments)
    if len(subreddit_list) > 1:
        logger.info(f'{len(subreddit_list)} total subreddits to scrape.')
    for i, sub in enumerate(tqdm(subreddit_list), start=1):
        logger.info(f'Scraping "{sub}" subreddit')
        posts_df, comments_df = scraper.scrape_subreddit(sub)
        logger.info(f'Saving {sub} posts data to {save_method}')
        scraper.save_choice(posts_df, save_method, table_name='posts', subreddit=sub)
        if include_comments:
            logger.info(f'Saving {sub} comments data to {save_method}')
            scraper.save_choice(comments_df, save_method, table_name='comments', subreddit=sub)
    logger.info('PROGRAM FINISHED')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='Subreddit Scraper',
                                     description='''
                                     This program scrapes any number of subreddits with or without comments.
                                     Choose subreddits to scrape, how to sort them, and how/where to save them.
                                     Use config files in this directory to configure scraper options.
                                     Documentation of the options is in the config files.
                                     Usage:
                                     > python RedditScraper.py --config example.ini''')

    parser.add_argument('--config', action='store',
                        help='Configuration file for scraper.')

    args = parser.parse_args()

    scraper_config = configparser.ConfigParser()
    scraper_config.read(args.config)

    project_name = scraper_config.get('SCRAPER', 'project_name')
    subreddit_list = [e.strip() for e in scraper_config.get(
        'SCRAPER', 'subreddit_list').split(',')]
    include_comments = scraper_config.getboolean('SCRAPER', 'include_comments')
    sorting = scraper_config.get('SCRAPER', 'sorting')
    save_method = scraper_config.get('SCRAPER', 'save_method')

    main()