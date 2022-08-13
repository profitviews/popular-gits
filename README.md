# Popular Gits

You know who you are.

Those popular people in high-school who most students tended to have mixed relationships with.  
As irritating as it was, you had to keep on their good sides and keep up with what they were doing.

Looking back, well, they weren't so bad.  Good on 'em really!  I would've if I could've.

This repo is is dedicated to the popular gits.

## Case Study

[Quant/Trading Projects](https://profitview.net/blog/open-source-trading-projects)

## How it works

In [Github](https://github.com) when you open a repo (like [popular-gits](https://github.com/profitviews/popular-gits)) 
in the top-right of your screen you will see a star glyph and the word "Star":

![Star example](/assets/images/github_top_right.png)

Click it - you've now "starred" the repo.  It's now be in _your_ list of stars.

These lists are accessible via the [Github API](https://docs.github.com/en/rest) and there is a [Python interface](https://github.com/PyGithub/PyGithub).

The idea of Popular Gits is that if a group of people like a particular repo, they probably have similar interests.
What if you listed _all_ the repos they like and worked out which are _most_ liked?
That's what we've done by looking at all the starred repos of everyone who starred that _particular_ repo.
We give the examples of [QuantLib](/Quantlib.md) and [ccxt](/ccxt.md).

**Note**: IT'S SLOW!  Due to the limitations on HTTP REST interfaces and understandable throttling by Github, 
a significant source repo of hundreds or thousands of stars will take a long time to run - 
typically many hours or a few days.

## Implementation

We use:
* the [Github API](https://docs.github.com/en/rest) and [PyGithub](https://github.com/PyGithub/PyGithub) (and, in small way, [Github Graph QL API](https://docs.github.com/en/graphql))
* [Sqlite](https://www.sqlite.org/index.html) with the [sqlite3](https://docs.python.org/3/library/sqlite3.html) Python package

## Installation

This is tested with Ubuntu Linux 22.04.  It should work with little effort on other Linuxen, MacOS and Windows.

1. Install [sqlite3](https://www.sqlite.org/download.html)
1. Install [Python](https://www.python.org/)
1. `pip install PyGithub`
1. Get a [Github account](https://github.com).  This is free and very easy.
   Once done, get a [Personal Access Token](https://github.com/settings/tokens).
1. To experiment with Popular Gits, install [Jupyter Lab](https://jupyter.org/install) and then use [our notebook](/popular_gits.ipynb) to start.
1. To use this notebook as-is, put your Personal Access Token in environment variable `GITHUB_KEY` via

   ```shell
   export GITHUB_KEY="<your Personal Access Token>"
   ```

   you might put this in your `~/.bashrc` or similar.


It will also be useful to install [SQLite Database Browser](https://sqlitebrowser.org/) so 
that you can easily create `.csv` files.

## Command Line

Use `pg.py` to run Poplular Gits on the command line (set it executable first):

```shell
chmod +x pg.py
./pg.py --github_key=<your key> pvcppdb profitviews cpp_crypto_algos
```

### Notes

1. You can **combine Githubs**: simply run it again with the same database
2. If it crashes or you want to stop it during a long run, that's fine: if you restart (without the `--reset` option) it will take up where it left off.

Other options are available.  Run `./pg.py --help`:

```
usage: pg.py [-h] [--reset]
             [--log {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
             [--github_key GITHUB_KEY] [--csv CSV_FILE]
             db_name org repo

positional arguments:
  db_name               Root name of SQLite database to be created or used
  org                   Github organization name
  repo                  Github repo name, i.e. github.com/org/repo

options:
  -h, --help            show this help message and exit
  --reset, -r           Erase the database on start if it exists
  --log {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}, -l {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
                        Specify the log level. Default is WARNING
  --github_key GITHUB_KEY, -k GITHUB_KEY
                        Specify your GitHub key. Otherwise it will look at
                        $GITHUB_KEY
  --csv CSV_FILE, -c CSV_FILE
                        Output data as CSV file
```

## Examples

We at [ProfitView](https://profitview.net) have run this code on a couple or repos, and here's some truncated results:
* [QuantLib](/Quantlib.md)
* [ccxt](/ccxt.md)

We also have [a blog](https://profitview.net/blog/open-source-trading-projects) on this process.

## Categorised Lists

While there may be some algorithmic ways to associate the repos, there's some value in checking their READMEs
and assigning a category.  We have done this for the [top 150 of the QuantLib set](/QuantlibStarredGithubs_Top150.csv) producing [QuantlibPopularLists.csv](/QuantlibPopularLists.csv).  This is useful for extracting "Top 10" lists and similar

## Notes
### Using Github's Graph QL API

The [Github Graph QL API](https://docs.github.com/en/graphql) can be used as an alternative to the main API when searching.  It would possibly have been a better choice for Popular Gits.
We used it in one part of the code the [`get_relative_popularity()`](https://github.com/profitviews/popular-gits/blob/69e78e4a19bc92f10b19dfb5ed22ec77582718af/categorise.py#L54) function in [categorise.py](https://github.com/profitviews/popular-gits/blob/main/categorise.py).  In this case it is because the main API restricts the maximum `totalCount` of starrers of a repo to 40K (for some reason).  In the UI there's no such limit.  It's possible just to scrape the page for this info, but Graph QL is more efficient.

#### You Need A New API Key

To use the API your need a Github API key with specific permissions.  Follow the normal [instructions for the the key](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token), but in step (8) when deciding the scopes, use the set [shown here](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql).

#### GQL in Python

For present purposes we want to use Python - [GQL](https://github.com/graphql-python/gql) is a good package.

The prototype connection to Github Graph QL is:
```python
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(
   url="https://api.github.com/graphql", 
   headers={'Authorization': f'token {os.environ["GITQL_KEY"]}'})
client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql('query { repository(owner:"profitviews", name:"popular-gits") {stargazerCount} }')

result = dict(client.execute(query))

totalCount = result['repository']['stargazerCount']
```

##### Asych Contexts

If you wish to run a query in an asynchronous context (such as a [Jupyter Notebook](https://jupyter.org/)) you can use:

```python
...
result = await client.execute_async(query)
```

If you want to write code that works in both contexts, you need to additionally:

```python
import asynchio
import nest_asyncio

nest_asycnio.apply()
...
# Put the query in an async function - `await` outside an async context is a syntax error
async def execute_query(client, query):
   result = await client.execute_async(query)
   return result
...
result = dict(asyncio.get_event_loop().run_until_complete(execute_query(client, query)))
totalCount = result['repository']['stargazerCount']
```

#### Exploring the Schema

You can download and explore the [public schema](https://docs.github.com/en/graphql/overview/public-schema).

There is also the very useful [Explorer](https://docs.github.com/en/graphql/overview/explorer) where you can run JSON queries directly.
