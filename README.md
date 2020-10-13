
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

    python scraper.py --config scraper_configs/python_test.ini

Using Pipenv

    pipenv run python scraper.py --config scraper_configs/python_test.ini


### Output to Log File

    python scraper.py --config scraper_configs/python_test.ini &>> python_test/scraper.log

## Requirements

pandas  
requests  
tqdm


## Credits

- https://www.datacamp.com/community/tutorials/scraping-reddit-python-scrapy
- https://www.osrsbox.com/blog/2019/03/18/watercooler-scraping-an-entire-subreddit-2007scape/
- https://data-flair.training/blogs/python-switch-case/
- https://jaxenter.com/implement-switch-case-statement-python-138315.html
- https://www.journaldev.com/15642/python-switch-case


## License

[MIT](https://tldrlegal.com/license/mit-license)

## Future Improvements

- Add S3 hooks
- Create wheel for pip install
- (Allow easier change of data directory)