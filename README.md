# DKIM archive website and tools

## In this repository

### DKIM archive website

See [dkim-lookup-app](dkim-lookup-app/)

### Fetch and upload script

The ```publish_records.py``` tool reads a list of domains and selectors, fetches the corresponding DKIM records via DNS lookup, and publishes the results to a database

### Mbox to TSV tool

As a complement to [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper), the ```mbox_to_tsv.py``` tool allows for fetching domains and selectors from emails from any provider via the Mbox archive format.
