# DKIM archive website

A website that lets the user search for a domain and returns archived DKIM selectors and keys for that domain

## Setup

```bash
yarn install
```

Copy `.env.example` to `.env` and configure the variables


## Running the development server

```bash
yarn dev
```

## Fetch DKIM keys from DNS and upload to database

The `update_records` script reads a list of domains and selectors, fetches the corresponding DKIM records via DNS lookup, and publishes the results to a database.

```bash
yarn update_records domains_and_selectors.tsv
```

A TSV file with domains and selectors can be created with the [mbox selector scraper](../util/mbox_selector_scraper.py)
or with [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper)

## Database management

Create the database from `schema.prisma`

```bash
yarn prisma db push
```

Start the Prisma Studio database manager

```bash
yarn prisma db studio
```

Calling the cron job on local development server

```bash
curl http://localhost:3000/api/batch_update -H "Accept: application/json" -H "Authorization: Bearer $CRON_SECRET"
```
