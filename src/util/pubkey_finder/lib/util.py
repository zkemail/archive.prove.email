from dataclasses import dataclass
import time


@dataclass
class ProgressReporter:
	total: int
	current: int
	last_printed_time: float = 0

	def increment(self):
		self.current += 1
		if time.time() - self.last_printed_time < 0.2:
			return
		self.last_printed_time = time.time()
		print(f'\r{self.current}/{self.total}', end='', flush=True)
