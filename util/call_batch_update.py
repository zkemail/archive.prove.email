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
#     */10 * * * * /path/to/call_batch_update.py /path/to/your_env_file.env | logger --tag DKIMREG

import os
import sys
import subprocess
import dotenv


def run_command(command: list[str]):
	return subprocess.check_output(command)


if __name__ == "__main__":

	if len(sys.argv) >= 2:
		env_file = sys.argv[1]
		if dotenv.load_dotenv(env_file) == True:
			print("loaded environment file: ", env_file)

	cron_secret = os.getenv('CRON_SECRET')
	if cron_secret == None:
		print("error: environment variable CRON_SECRET not found")
		sys.exit(1)

	cmd = ['curl', 'https://registry.prove.email/api/batch_update', '-H', 'Accept: application/json', '-H', 'Authorization: Bearer ' + cron_secret]
	res = run_command(cmd)
	print(res)
