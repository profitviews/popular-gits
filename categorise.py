import os
import csv
import asyncio
import nest_asyncio
from itertools import combinations
from collections import defaultdict
from github import Github
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

def get_popularity_lists(categorized_popularity_file):
    """ From a CSV file created from popular_gits.py's 'gits' database table
    with structure like:
        || URL                                 || Count || Categories ||
        |  github.com/profitviews/popular-gits |  123   | App,Python  |

    create a dictionary of lists of URLs in order of populariy keyed on category combinations 

    Args:
    categorized_popularity_file: the CSV file with structure as above
    """
    popularity_lists = defaultdict(list)
    with open(categorized_popularity_file) as csvfile:
        for git in csv.DictReader(csvfile):
            c = git['Categories'].split(',')
            for l in range(1,len(c)):
                for s in combinations(c, l):
                    popularity_lists[tuple(sorted(s))].append((git['URL'],git['Popularity']))
    return popularity_lists


def create_popularity_list_file(popularity_lists, popularity_list_file):
    """ Given a dictionary of lists of URLs and counts keyed on category combinations
    create a CSV file of category combinations to popular URLs
    The output will be like:
        || Category combination || URL                                 ||
        | App,Python            |  github.com/odoo/odoo                |
        | App,Python            |  github.com/profitviews/popular-gits |
    
    Args:
        popularity_lists: dictionary of lists of URLs with counts keyed on category combinations
        popularity_list_file: output CSV file
    """
    with open(popularity_list_file, 'w') as csvfile:
        pl = csv.writer(csvfile)
        pl.writerow(['Categories', 'URL'])
        for l,r in popularity_lists.items():
            cts = ",".join(l)
            r = sorted(r, key=lambda rep: rep[1], reverse=True)
            for repo,_ in r:
                pl.writerow([cts,repo])


def get_relative_popularity(popularity_file, output_file):
    """ From a CSV file with GitHub URL and Popularity, get the overall stars for the URL
    and calculate the relative popularity.
    Create a new CSV with relative popularity and overall stars

    Args:
        popularity_file: must have columns URL and Popularity
        output_file: add columns OverallStars and RelativePopularity
    """

    nest_asyncio.apply()
    # We need the GraphQL API to get the count of Stargazers when over 40K
    transport = AIOHTTPTransport(
        url="https://api.github.com/graphql", 
        headers={'Authorization': f'token {os.environ["GITQL_KEY"]}'})
    client = Client(transport=transport, fetch_schema_from_transport=True)

    async def execute_query(client, query):  # So it works in Jupyter and other async contexts
        result = await client.execute_async(query)
        return result
    
    with open(popularity_file) as pop_file, open(output_file, 'w') as rel_pop:
        gits = csv.DictReader(pop_file)
        r = csv.writer(rel_pop)
        r.writerow(gits.fieldnames + ['OverallStars', 'RelativePopularity'])
        g = Github(os.environ['GITHUB_KEY'])
        for git in gits:
            repo_id = git['URL'].split('.com/')[1]
            repo = g.get_repo(repo_id)
            owner,name = repo_id.split('/')
            if (rc := repo.get_stargazers().totalCount) >= 40_000:  # Magic max cut-off
                query = gql(f'query {{ repository(owner:"{owner}", name:"{name}") {{stargazerCount}} }}')
                # See execute_query: lets it work in Jupyter and other async contexts
                rc = dict(asyncio.get_event_loop().run_until_complete(execute_query(client, query)))['repository']['stargazerCount']
                print(f"Repo count: {rc}")
            r.writerow(list(git.values()) + [rc, int(git['Popularity'])/rc])
