# DKIM archive website

A website that lets the user search for a domain and returns archived DKIM selectors and keys for that domain

## Setup

```
yarn install
```

Copy ```.env.example``` to ```.env``` and configure database URLs


Run the development server

```
yarn dev
```

## Database management

Create the database from ```schema.prisma```

```
yarn prisma db push
```

Start the Prisma Studio database manager

```
yarn prisma db studio
```
