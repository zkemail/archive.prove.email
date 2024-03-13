#!/usr/bin/env python3

# This script is used to call the batch_update API endpoint
# Usage: call_batch_update.py [env_file.env]

# Example installation and configuration on Ubuntu:
#
# sudo apt install python3-pip
# sudo apt install curl
# pip install python-dotenv
#
# Set the environment variable CRON_SECRET in the environment or in a .env file.
# Run "crontab -e" and add the following line:
#
#     */10 * * * * /path/to/call_batch_update.py --env-file /path/to/env_file.env --batch-size 20 | logger --tag DKIMREG

import argparse
import os
import sys
import subprocess
import dotenv
from urllib.parse import urlencode
from urllib.parse import urljoin


def run_command(command: list[str]):
	return subprocess.check_output(command)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--env-file", type=str, help="the environment file that contains the CRON_SECRET variable")
	parser.add_argument("--batch-size", type=int, default=10, help="the number of records to update on the server")
	parser.add_argument("--domain", type=str, default="https://registry.prove.email")
	args = parser.parse_args()

	if args.env_file:
		env_file = args.env_file
		if dotenv.load_dotenv(env_file) == True:
			print("loaded environment file: ", env_file)

	cron_secret = os.getenv('CRON_SECRET')
	if cron_secret == None:
		print("error: environment variable CRON_SECRET not found")
		sys.exit(1)

	url = urljoin(args.domain, '/api/batch_update?' + urlencode({'batch_size': args.batch_size}))
	print(f'calling {url}')
	cmd = ['curl', url, '-H', 'Accept: application/json', '-H', 'Authorization: Bearer ' + cron_secret]
	res = run_command(cmd)
	print(res.decode('utf-8'))
