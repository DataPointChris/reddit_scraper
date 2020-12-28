
<h1 align="center">
  Reddit Scraper
  <br>
</h1>


## Features

* Scrapes a single or list of subreddits using a simple configuration file.
* Option to include post comments
* Saves data as CSV, SQLite (Postgres, MongoDB, MySQL, S3 frameworks included but not fully functioning)
* Easily run scraper on a schedule.


## Installation

    git clone https://github.com/DataPointChris/reddit_scraper.git
    cd reddit_scraper
   
If you have Pipenv installed:

    pipenv sync

Using Pip

    pip install -r requirements.txt


## How To Use

    python scraper.py --config scraper_configs/example.ini

Using Pipenv

    pipenv run python scraper.py --config scraper_configs/example.ini


## Requirements

pandas  
requests  
tqdm


## License

[MIT](https://tldrlegal.com/license/mit-license)


## Future Improvements

- Add S3 hooks
- Create wheel for pip install
- (Allow easier change of data directory)