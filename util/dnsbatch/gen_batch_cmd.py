#!.venv/bin/python

import os
import sys


def run():
	output_dir = sys.argv[1]
	print('set -e')
	print('set -o xtrace')
	for i in range(100):
		input_file = f'mm{i:02d}'
		output_file = f'{output_dir}/{input_file}.out'
		tmp_output_file = f'{input_file}.out.tmp'
		if os.path.exists(output_file):
			print(f'# {output_file} exists')
			print()
			continue
		print(
		    f".venv/bin/modal run dsp_onetime_batch.py --domains-filename dnsbatch/mm/{input_file} --selectors-filename dnsbatch/merged.txt --no-sparse | grep '^DNS_BATCH_RESULT,' > {tmp_output_file}"
		)
		print(f"mv {tmp_output_file} {output_file}")
		print()


if __name__ == "__main__":
	run()
