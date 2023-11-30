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

```
yarn update_records domains_and_selectors.tsv
```

A tsv file with domains and selectors can be created with ```mbox_to_tsv.py```

## Database management

Create the database from ```schema.prisma```

```
yarn prisma db push
```

Start the Prisma Studio database manager

```
yarn prisma db studio
```
