
import csv
from itertools import combinations
from collections import defaultdict


def get_popularity_lists(categorized_popularity_file):
    """ From a CSV file created from popular_gits.py's 'gits' database table
    with structure like:
        || URL                                 || Count || Categories ||
        |  github.com/profitviews/popular-gits |  123   | App,Python  |

    create a dictionary of lists of URLs in order of populariy keyed on category combinations 

    Args:
    categorized_popularity_file: the CSV file with structure as above
    """
    pop_lists = defaultdict(list)
    with open(categorized_popularity_file) as csvfile:
        for git in csv.DictReader(csvfile):
            c = git['Categories'].split(',')
            for l in range(1,len(c)):
                for s in combinations(c, l):
                    pop_lists[tuple(sorted(s))].append((git['URL'],git['Popularity']))
    return pop_lists


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
