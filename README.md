
HYPER
-----------
Modules required: BeautifulSoup, requests

### COMMAND LINE INTERFACE (CLI)
Defaults to scraping the 'Popular' Hype Machine (hypem.com) songs when the script is run.

To run the application, with the aforementioned default

```python myHype.py```

If you would like to search a particular artist or song

```python myHype.py Beatles```

If you would like to serach by hypem username

```python myHype.py user: username```


After choosing the desired song selections, the script shows the progress of each download, exiting when all requested songs have finished downloading.


### DESIGN
This script uses 'threading' to download requested songs simultaneously
