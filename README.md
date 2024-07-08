This repository is part of the [Proof of Email](https://prove.email/) project

# DKIM archive website

The website lets the user search for a domain and returns archived DKIM selectors and keys for that domain. Visit the website at https://archive.prove.email/

Under `/contribute`, users can contribute with new domains and selectors, which are extracted from the `DKIM-Signature` header field in each email message in the user's Gmail account.

When domains and selectors are added, the site fetches the DKIM key via DNS and stores it in the database.

For each record, the site also generates an on-chain proof with [Witness](https://witness.co), which functions as a data availability timestamp.

## Development
For information on how to help with development, see [development.md](development.md).

## Domain search API

A public API endpoint for fetching keys for a certain domain is available at `https://archive.prove.email/api/key?domain={domain_name}`. The response will contain a list of all known selectors and DKIM keys for `domain_name` and its subdomains.

An example call from the command line:

```bash
curl "https://archive.prove.email/api/key?domain=ethereum.org" | python -m json.tool
```

<a name="mailbox_scraper"></a>

## Extract domains and selectors from an exported mailbox

The scraper tools (src/util/mbox_scraper.py` and `(src/util/pst_scraper.py`) allow for extacting domains and selectors
from the messages in an email account from any provider, by scraping a file that is exported from the mail account.

### 1. Export email messages

#### a. From Gmail

Go to https://takeout.google.com/settings/takeout and click **Deselect all**, then scroll down and select **Mail**, click **Next step**, and leave the default settings for the export format. When you click **Create export**, you will then get an email in the next few days with a link to download a .mbox file with all your email messages. Download it within 7 days to avoid expiration.

#### b. From Outlook

Go to https://outlook.live.com/mail/0/options/general/export/exportMailbox and click **Export Mailbox**.
It will say 'Status: Export in Progress", then you will get an email in the next few days with a download link to a .pst file.
Continue with [extracting domains and selectors](#archive_extract) from the file.


#### c. From other email providers

The easiest option is if your email provider's web client lets you export emails as an .mbox or a .pst file.
You can then use that feature and continue with [extracting domains and selectors](#archive_extract).

If no export feature is available, an alternative is to connect your email account to a client such as Mozilla Thunderbird, Gnome Evolution or Microsoft Outlook, and use the export feature from within the email client.

<a name="archive_extract"></a>

### 2. Extract domains and selectors

When you have obtained an .mbox or a .pst file, use `mbox_scraper.py` or `pst_scraper.py` to extract the domains and selectors

Example for .mbox files:

```bash
python3 src/util/mbox_scraper.py inbox.mbox > domains_and_selectors.tsv
```

Example for .pst files:

```bash
pip3 install libpff-python
python3 src/util/pst_scraper.py inbox.pst > domains_and_selectors.tsv
```

The output file, (`domains_and_selectors.tsv` in the examples above), is a [TSV](https://en.wikipedia.org/wiki/Tab-separated_values) file with two columns: domain and selector.

You can now use the .tsv file to contribute to the archive on the [Upload from TSV file](https://archive.prove.email/upload_tsv) page.
