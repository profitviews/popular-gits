#!/usr/bin/env python

from distutils.log import INFO
import popular_gits
import os
import argparse
import logging

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument('db_name', help="Root name of SQLite database to be created or used")
parser.add_argument('org', help="Github organization name")
parser.add_argument('repo', help="Github repo name, i.e. github.com/org/repo")
parser.add_argument('--reset', '-r', help="Erase the database if it exists", action="store_true")
parser.add_argument('--log', '-l', choices=logging._nameToLevel.keys() , help=f"Specify the log level.  Default is {logging._levelToName[logging.getLogger().__dict__['level']]}")

if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger()

    if args.log:
        logger.setLevel(args.log)
    logger.info("Starting popular_gits")
    pg = popular_gits.popular_gits(args.db_name, os.environ['GITHUB_KEY'], args.org, args.repo, logger)
    if args.reset:
        pg.reset()
    
    pg.run()
