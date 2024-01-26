# DKIM archive website

A website that lets the user search for a domain and returns archived DKIM selectors and keys for that domain.
Visit the website at https://dkim-lookup.onrender.com/

## Local development

```bash
yarn install
```

Access to a [PostgreSQL](https://www.postgresql.org/) database is needed for development.

Copy `.env.example` to `.env` and configure the variables

Initialize the database from `schema.prisma`

```bash
yarn prisma migrate deploy
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

## Batch updates

The API endpoint `/api/batch_update` is designed to be called at regular intervals, for example as a cron job.
The function updates the *N* oldest database records via DNS lookups.
Enable the feature by defining *N* through the `BATCH_UPDATE_NUM_RECORDS` environment variable.

To manually call `batch_update` on a local development server, run:

```bash
curl http://localhost:3000/api/batch_update -H "Accept: application/json" -H "Authorization: Bearer $CRON_SECRET"
```

To manually call `batch_update` on a production server on example.com, run:

```bash
curl https://example.com/api/batch_update -H "Accept: application/json" -H "Authorization: Bearer $CRON_SECRET"
```
