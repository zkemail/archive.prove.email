#!/usr/bin/env python
import os
import psycopg2
from dotenv import load_dotenv
import sqlite3
import dns.resolver
import dns.rdatatype

load_dotenv()

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        conn = psycopg2.connect(database="dkim_lookup", user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print(cur.fetchone())
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


'''
decode a DNS DKIM record such as "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUA"
to a dict: {'v': 'DKIM1', 'k': 'rsa', 'p': 'MIGfMA0GCSqGSIb3DQEBAQUA'}
'''
def decode_dkim_record(dkimData):
    parts = list(map(lambda x: x.strip(), dkimData.split(';')))
    res = {}
    for part in parts:
        key, value = part.split('=')
        res[key] = value
    return res

def run():
    connect()
    domainSelectorsDict = get_domain_selectors_dict()
    print(domainSelectorsDict)
    for domain in domainSelectorsDict:
        print('DOMAIN', domain)
        for selector in domainSelectorsDict[domain]:
            print('SELECTOR', selector)
            response = dns.resolver.resolve(f'{selector}._domainkey.{domain}', 'TXT')
            records = []
            for row in response:
                dkimData = b''.join(row.strings).decode()
                print(dkimData)
                records.append(dkimData)
            if len(records) == 0:
                print('NO RECORDS FOUND')
                continue
            if len(records) > 1:
                print('warning: > 1 record found, using first one')
            decoded_dkim_data = decode_dkim_record(records[0])
            print(decoded_dkim_data)


run()