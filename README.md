# Competitor Blog Analysis Pipeline

An automated data pipeline and analytics dashboard built for an early-stage startup competing in the video review and collaboration space (such as competing with **Frame.io**). This tool scrapes competitor blogs, parses HTML content using structural landmarks (classes and IDs), calculates engagement and content metrics, stores the processed data, and displays insights via a lightweight web dashboard.


##  Pipeline Architecture

The project follows a robust, multi-stage data flow:

```text
[ Download Articles ] ──> [ Parse Content ] ──> [ Compute Analytics ] ──> [ Store Data ] ──> [ Dashboard ]
    (requests)             (BeautifulSoup)      (Python Standard)          (JSON)            (Flask)
```

1. **Download Articles (`requests`)**: Programmatically fetches raw HTML pages from competitor blogs, traversing categories and navigating pagination.
2. **Parse Content (`Beautiful Soup`)**: Uses HTML and CSS selectors (classes and IDs) to extract titles, authors, dates, categories, reading times, featured images, and body content.
3. **Compute Analytics (`Python Standard`)**: Aggregates metrics such as publishing cadence per category, average article length, media density, and reading times.
4. **Store Data (`JSON`)**: Persists structured metrics and raw extracted data locally into JSON format.
5. **Dashboard (`Flask`)**: Serves an interactive web interface to explore competitor insights and trends.


## Features

* **Automated Web Scraping**: Scale data collection beyond manual browsing to capture complete article catalogs and archives.
* **Granular Content Parsing**: Isolates article text from structural wrappers using HTML tags, classes, and IDs.
* **Category & Cadence Analytics**: Track how frequently competitors post across different categories and analyze content length trends.
* **Local Data Persistence**: Clean, structured storage using lightweight JSON files.
* **Interactive Web Dashboard**: Built with Flask to visualize metrics cleanly in your browser.

## License
This project is open-source and available under the [MIT License](LICENSE).