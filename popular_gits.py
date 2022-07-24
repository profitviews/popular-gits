
import sqlite3
import time
import requests
import logging
import csv
from github import Github, RateLimitExceededException, GithubException, BadCredentialsException
from collections import defaultdict
from datetime import datetime
from contextlib import closing


logging.basicConfig()

class popular_gits():
    """Popular Gits - you know who you are.
    
    Objects of this class encapsulate a Github repo and its "stargazers": 
    those Github users who have "starred" the repo indicating their positive interest in it:
    those repos are popular.

    The theory is that the *other* repos these people have starred are likely to be of
    interest to the other starrers of the repo.  The *most* starred should be of most interest.

    This code creates a database table
    || Org || Repo || Count ||
    so that repo http://github.com/{Org}/{Repo} will have {Count} starrers of the original repo.
    """

    page_size = 30

    def __init__(self, db_name, github_key, repo_org, repo_name, logger=logging.getLogger()):
        """Set up a repo to find its popular gits
        
        db_name: the name of the SQLite database that will be created (or accessed)
        github_key: the Github Access Token that will be used to run the Github API functions
        repo_org: the 'repo_org' part of https://github.com/{repo_org}/{repo_name}
        repo_name: the 'repo_name' part
        """
        self._setUp = False
        self._db_name = db_name
        self._repo_org = repo_org
        self._repo_name = repo_name
        self._logger=logger
        try:
            g = Github(github_key)
            self._repo = g.get_repo(self.repo_id)
        except BadCredentialsException:
            self._logger.error("Failed to authenticate Github: your key is probably incorrect")
        else:
            self.gits = defaultdict(int)
            self.con = sqlite3.connect(f'{self._db_name}.db')
            self.__setup_db()
            self._setUp = True
    

    @property
    def setUp(self):
        return self._setUp


    def __setup_db(self):
        with closing(self.con.cursor()) as cur:
            cur.execute('create table if not exists users (login text PRIMARY KEY, date text)')
            cur.execute('create table if not exists gits (org text UNIQUE, repo text UNIQUE, count int)')
            self.con.commit()
            self._logger.info(f"Database {self._db_name} with tables 'users' and 'gits' exists")

    def reset(self):
        """Remove all the data in the database and set it up again"""
        with closing(self.con.cursor()) as cur:
            cur.execute("drop table users")
            cur.execute("drop table gits")
            self.con.commit()
        self.__setup_db()
        self._logger.info(f"Recreated database {self._db_name}")

    @property
    def repo_id(self):
        return f"{self._repo_org}/{self._repo_name}"

    def get_gits(self):
        """Extract the existing set of starry gits from the database into a dictionary"""
        cur = self.con.cursor()
        with closing(self.con.cursor()) as cur:
            cur.execute("select * from gits")
            while f := cur.fetchmany():
                for o, rp, c in f:
                    self.gits[(o,rp)]=c

    def populate_user_gits(self, u):
        """Given a user, find all their starry gits and put them in the database
           
           It will only commit if there's no failure
        """
        new_gits = defaultdict(int)
        starred = u.get_starred()
        # Exclude those who star more than 1000 repos - this couldn't be done thoughtfully
        if starred.totalCount > 1000:
            page_count = 0
            self._logger.info(f"Excluded user {u.login} because they starred {starred.totalCount} repos")
        else:
            page_count = starred.totalCount
        for spage in (starred.get_page(i) for i in range(0, page_count//popular_gits.page_size+1)):
            for s in spage:
                o, rp = s.full_name.split('/')
                self.gits[(o,rp)]+=1
                new_gits[(o,rp)] = self.gits[(o,rp)]
        with closing(self.con.cursor()) as cur:
            cur.execute("insert into users values(?, ?)", (u.login, datetime.today().strftime('%Y-%m-%d')))
            for (o, rp), c in new_gits.items():
                cur.execute("replace into gits (org, repo, count) values(?, ?, ?)", (o, rp, c))
            self.con.commit()

    def accumulate_gits(self):
        """For all the repo's stargazers, if their repos haven't already been accumulated, do it now"""
        self.get_gits()
        with closing(self.con.cursor()) as cur:
            paged = self._repo.get_stargazers()
            pages = (paged.get_page(i) for i in range(0, paged.totalCount//popular_gits.page_size+1))
            for page in pages:
                for u in page:
                    cur.execute("select * from users where login=:login", {"login": u.login})
                    if not cur.fetchone(): # No such user yet
                        self.populate_user_gits(u)

    def run(self):
        """Tolerate the various "normal exceptions" """
        while(True):  # After each exception have another go until finished or interrupt
            try:
                self.accumulate_gits()
                return
            except KeyboardInterrupt:
                self._logger.info("Interrupted - pausing")
                break
            except requests.exceptions.ReadTimeout as rto:
                self._logger.warning(f"Timeout {rto=}, {type(rto)=}.  Sleeping for 1 minute")
                time.sleep(60)
            except RateLimitExceededException as ree:
                rate_limit = int(ree.headers['x-ratelimit-limit'])
                reset_seconds = int(ree.headers['x-ratelimit-reset']) - int(time.time())
                self._logger.warning(f"Rate Limit {rate_limit} breeched.  Resetting in {reset_seconds + 5} seconds")
                time.sleep(reset_seconds + 5)
            except GithubException as ge:
                self._logger.warning(f"Github exception {ge=}, {type(ge)=}.  Sleeping for 1 minute")
                time.sleep(60)
            except BaseException as err:
                self._logger.error(f"Error {err=}, {type(err)=}.  Exiting")
                break

    def gits_csv(self, git_file):
        """Write results to CSV file"""
        cur = self.con.cursor()
        with closing(self.con.cursor()) as cur, open(git_file, 'w') as git_csv:
            gc = csv.writer(git_csv)
            cur.execute("select * from gits order by count desc")
            while f := cur.fetchmany():                
                for o, rp, c in f:
                    gc.writerow([f"https://github.com/{o}/{rp}", c])
