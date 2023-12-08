# DKIM archive website and tools

These tools are in contribution to [ZK Email](https://github.com/zkemail/zk-email-verify),
and in particular this [issue](https://github.com/zkemail/zk-email-verify/issues/81).

## In this repository

### DKIM archive website

Website for searching archived DKIM selectors. It also contains a tool (`yarn update_records`) to fetch new keys via DNS.

See [dkim-lookup-app](dkim-lookup-app/)

### Mbox selector scraper

As a complement to [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper),
the [mbox selector scraper](util/mbox_selector_scraper.py) allows for fetching domains and selectors from emails from any provider via the mbox format.
