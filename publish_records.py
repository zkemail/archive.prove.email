#!/usr/bin/env python
import os
from datetime import datetime
from typing import NamedTuple
import sqlite3
import psycopg2
import dns.resolver
import dns.rdatatype
from dotenv import load_dotenv


class DkimRecord(NamedTuple):
    domain: str
    selector: str
    value: str
    timestamp: datetime


def get_os_env(key: str):
    value = os.getenv(key)
    if not value:
        raise Exception(f'environment variable {key} not found')
    return value


def add_records_to_db(records: list[DkimRecord]):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        conn = psycopg2.connect(
            host=get_os_env('POSTGRESQL_HOST'),
            database=get_os_env('POSTGRESQL_DATABASE'),
            user=get_os_env('POSTGRESQL_USER'),
            password=get_os_env('POSTGRESQL_PASSWORD'))
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print(cur.fetchone())
        for record in records:
            cur.execute('SELECT * FROM "DkimRecord" WHERE "dkimDomain" = %s AND "dkimSelector" = %s',
                        (record.domain, record.selector))
            if cur.fetchone():
                print(f'{record.domain}, {record.selector} already exists, skipping')
                continue
            print(f'adding {record.domain}, {record.selector} to database')
            cur.execute('INSERT INTO "DkimRecord" ("dkimDomain", "dkimSelector", "fetchedAt", "value") VALUES (%s, %s, %s, %s)',
                        (record.domain, record.selector, record.timestamp, record.value))
            conn.commit()
        cur.close()
    except (psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


def connect_to_sqlite3_db():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    conn.commit()
    return c, conn


def get_domain_selectors_dict():
    c, conn = connect_to_sqlite3_db()
    c.execute('SELECT dkimSelector, dkimDomain FROM emails')
    raw_results = list(set(c.fetchall()))
    print(raw_results)
    conn.close()
    res = {}
    for selector_domain in raw_results:
        selector, domain = selector_domain
        if (not selector) or (not domain):
            continue
        if domain not in res:
            res[domain] = []
        if selector not in res[domain]:
            res[domain].append(selector)
    return res


def fetch_dkim_records_from_dns(domainSelectorsDict):
    res = []
    domainSelectorsDict = get_domain_selectors_dict()
    for domain in domainSelectorsDict:
        for selector in domainSelectorsDict[domain]:
            print(f'fetching {selector}._domainkey.{domain}')
            qname = f'{selector}._domainkey.{domain}'
            response = dns.resolver.resolve(qname, 'TXT')
            if len(response) == 0:
                print(f'warning: no records found for {qname}')
                continue
            if len(response) > 1:
                print(
                    f'warning: > 1 record found for {qname}, using first one')
            dkimData = b''.join(response[0].strings).decode()
            dkimRecord = DkimRecord(
                selector=selector, domain=domain, value=dkimData, timestamp=datetime.now())
            res.append(dkimRecord)
    return res


def main():
    load_dotenv()
    print('loading domains and selectors')
    domainSelectorsDict = get_domain_selectors_dict()
    print('fetching dkim records from dns')
    records = fetch_dkim_records_from_dns(domainSelectorsDict)
    print('adding records to database')
    add_records_to_db(records)


if __name__ == '__main__':
    main()
