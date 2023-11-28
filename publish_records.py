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
    dkimSelector: str
    dkimDomain: str
    value: str
    timestamp: datetime


def getOsEnv(key: str):
    value = os.getenv(key)
    if not value:
        raise Exception(f'environment variable {key} not found')
    return value


def addRecordsToDb(records: list[DkimRecord]):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        conn = psycopg2.connect(
            host=getOsEnv('POSTGRESQL_HOST'),
            database=getOsEnv('POSTGRESQL_DATABASE'),
            user=getOsEnv('POSTGRESQL_USER'),
            password=getOsEnv('POSTGRESQL_PASSWORD'))
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print(cur.fetchone())
        for record in records:
            print(record)
            cur.execute('SELECT * FROM "DkimRecord" WHERE "dkimSelector" = %s AND "dkimDomain" = %s',
                        (record.dkimSelector, record.dkimDomain))
            if cur.fetchone():
                print('record already exists')
                continue
            cur.execute('INSERT INTO "DkimRecord" ("dkimSelector", "dkimDomain", "fetchedAt", "value") VALUES (%s, %s, %s, %s)',
                        (record.dkimSelector, record.dkimDomain, record.timestamp, record.value))
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


def getDkimRecords():
    res = []
    domainSelectorsDict = get_domain_selectors_dict()
    print(domainSelectorsDict)
    for domain in domainSelectorsDict:
        print('DOMAIN', domain)
        for selector in domainSelectorsDict[domain]:
            print('SELECTOR', selector)
            qname = f'{selector}._domainkey.{domain}'
            response = dns.resolver.resolve(qname, 'TXT')
            if len(response) == 0:
                print(f'warning: no records found for {qname}')
                continue
            if len(response) > 1:
                print(
                    f'warning: > 1 record found for {qname}, using first one')
            dkimData = b''.join(response[0].strings).decode()
            print(dkimData)
            dkimRecord = DkimRecord(
                dkimSelector=selector, dkimDomain=domain, value=dkimData, timestamp=datetime.now())
            res.append(dkimRecord)
    return res


def run():
    load_dotenv()
    records = getDkimRecords()
    addRecordsToDb(records)


run()
