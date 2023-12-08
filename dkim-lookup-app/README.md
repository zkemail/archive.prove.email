# DKIM archive website

A website that lets the user search for a domain and returns archived DKIM selectors and keys for that domain

## Setup

```
yarn install
```

Copy ```.env.example``` to ```.env``` and configure database URLs


## Running the development server

```
yarn dev
```

## Fetch DKIM keys from DNS and upload to database

The ```update_records``` script reads a list of domains and selectors, fetches the corresponding DKIM records via DNS lookup, and publishes the results to a database.

```
yarn update_records domains_and_selectors.tsv
```

A TSV file with domains and selectors can be created with the [mbox selector scraper](../util/mbox_selector_scraper.py)
or with [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper)

## Database management

Create the database from ```schema.prisma```

```
yarn prisma db push
```

Start the Prisma Studio database manager

```
yarn prisma db studio
```
