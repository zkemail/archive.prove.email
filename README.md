# DKIM archive website and tools

These tools are in contribution to [ZK Email](https://github.com/zkemail/zk-email-verify),
and in particular this [issue](https://github.com/zkemail/zk-email-verify/issues/81).


## Website

The website lets the user search for a domain and returns archived DKIM selectors and keys for that domain. Visit the website at https://registry.prove.email/

Under `/upload`, users can contribute with new domains and selectors, which are extracted from the `DKIM-Signature` header field in each email message in the user's Gmail account.

### Local development

```bash
cd dkim-lookup-app
yarn install
```

Access to a [PostgreSQL](https://www.postgresql.org/) database is needed for development. See [below](#ubuntu_postgresql) for an example setup of PostgreSQL on Ubuntu.

Copy `.env.example` to `.env` and configure the variables

Initialize the database from `schema.prisma`

```bash
yarn prisma migrate deploy
```

Start the development server

```bash
yarn dev
```

<a name="ubuntu_postgresql"></a>
#### Setting up a PostgreSQL database on Ubuntu

Install PostgreSQL server and client with `sudo apt install postgresql`

Log in with `sudo -u postgres psql` and set a password with `\password postgres`

Test the login: `psql postgresql://postgres:YOURPASSWORD@localhost`

Your `.env` config would now be:

```
POSTGRES_URL_NON_POOLING="postgresql://postgres:YOURPASSWORD@localhost/dkim_lookup"
POSTGRES_PRISMA_URL="postgresql://postgres:YOURPASSWORD@localhost/dkim_lookup"
```

### Database management

Start the Prisma Studio database manager

```bash
yarn prisma db studio
```

Resetting the database

```bash
yarn prisma migrate reset
```

### Fetch DKIM keys from DNS and upload to database

The `update_records` script reads a list of domains and selectors, fetches the corresponding DKIM records via DNS lookup, and publishes the results to a database.

```bash
yarn update_records domains_and_selectors.tsv
```

A TSV file with domains and selectors can be created with the [mbox selector scraper](../util/mbox_selector_scraper.py)
or with [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper)


### Batch updates

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

## Tools

### Mbox selector scraper

As a complement to [Gmail Metadata Scraper](https://github.com/zkemail/selector-scraper),
the [mbox selector scraper](util/mbox_selector_scraper.py) allows for fetching domains and selectors from emails from any provider via the mbox format.
