#!.venv/bin/python

import os

def run():
	for i in range(100):
		input_file = f'mm{i:02d}'
		output_file = f'dnsbatch/mm/{input_file}.out'
		if os.path.exists(output_file):
			print(f'# {output_file} exists')
			continue
		batch_cmd = f".venv/bin/modal run dsp_onetime_batch.py --domains-filename dnsbatch/mm/{input_file} --selectors-filename dnsbatch/merged.txt --no-sparse | grep '^DNS_BATCH_RESULT,' > {output_file}"
		print(batch_cmd)

if __name__ == "__main__":
	run()
