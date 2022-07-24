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
parser.add_argument('--reset', '-r', help="Erase the database on start if it exists", action="store_true")
parser.add_argument('--log', '-l', choices=logging._nameToLevel.keys() , help=f"Specify the log level.  Default is {logging._levelToName[logging.getLogger().__dict__['level']]}")
parser.add_argument('--github_key', '-k', help=f"Specify your GitHub key.  Otherwise it will look at $GITHUB_KEY")
parser.add_argument('--csv', '-c', help="Output data as CSV file", metavar="CSV_FILE")

if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger()

    if args.log:
        logger.setLevel(args.log)
    logger.info("Starting popular_gits")
    pg = popular_gits.popular_gits(args.db_name, args.github_key if args.github_key else os.environ['GITHUB_KEY'], args.org, args.repo, logger)
    if args.reset:
        pg.reset()
    
    if pg.setUp:
        pg.run()

        if args.csv:
            pg.gits_csv(args.csv)

    else:
        logger.warn("Data not processed: not properly set up")