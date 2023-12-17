# DKIM archive website

A website that lets the user search for a domain and returns archived DKIM selectors and keys for that domain

## Local development

```bash
yarn install
```

Access to a [PostgreSQL](https://www.postgresql.org/) database is needed for development.

Copy `.env.example` to `.env` and configure the variables

Initialize the database from `schema.prisma`

```bash
yarn prisma db push
```

Start the development server

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

Start the Prisma Studio database manager

```bash
yarn prisma db studio
```

Resetting the database

```bash
yarn prisma migrate reset
```

## Batch update cron job

Calling the `batch_update`` cron job on local development server

```bash
curl http://localhost:3000/api/batch_update -H "Accept: application/json" -H "Authorization: Bearer $CRON_SECRET"
```

Calling the `batch_update`` cron job on production server

```bash
curl https://dkim-lookup.vercel.app/api/batch_update -H "Accept: application/json" -H "Authorization: Bearer $CRON_SECRET"
```