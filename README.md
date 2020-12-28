
<h1 align="center">
  Reddit Scraper
  <br>
</h1>


## Features

* Scrapes a single or list of subreddits using a simple configuration file.
* Option to include post comments
* Saves data as CSV, SQLite, or S3
* Easily run scraper on a schedule.


## Installation

### Clone the repo
```bash
git clone https://github.com/DataPointChris/reddit_scraper.git
cd reddit_scraper
```

### Using Poetry to Install
```bash
poetry install  
poetry run python scraper.py --config scraper_configs/example.ini
```

### Using Pip to Install
```bash
python -m venv scraper_venv  
source scraper_venv/bin/activate
pip install -r requirements.txt
python scraper.py --config scraper_configs/example.ini
```


## License

[MIT](https://tldrlegal.com/license/mit-license)


## Future Improvements

- [ ] Create wheel for pip install
- [ ] Allow easier change of data directory