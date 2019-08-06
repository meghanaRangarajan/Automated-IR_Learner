import pigpio
import asyncio
import functools
from os import system

class necd:
	def __init__(self):
                self.callback = None
                self.pin_callback = None
                self.frames = list()
                self._sensor_pin = None
                self.frequency = 0
                self.protocol_id = list()

	def init(self, pi, pin):
		self.pi = pi
		self.loop = asyncio.get_event_loop()
		self._sensor_pin = pin

	def shutdown(self):
		self.pi.set_watchdog(self._sensor_pin, 0)
		if self.pin_callback is not None:
			self.pin_callback.cancel()
			self.pin_callback = None

	def _pin_callback_entry(self, gpio, level, tick):
		if level == 2:
			if len(self.frames) < 5:
				# Short sequence. Discard
				print("Discarding Short Sequence")
				self.pi.set_watchdog(self._sensor_pin, 0)
				self.frames = list()
				return
			# Watchdog expired.
			self.loop.call_soon_threadsafe(functools.partial(self._analyse_ir_pulses))
			self.disable()
			return

		if len(self.frames) == 0:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)
		if len(self.frames) == 1:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)

		self.frames.append((level, tick))

	def _decode_ir_sequence(self):
		# Signal is active low. Hence the lead in is a -ve edge
		sequence = []
		first_tick = 0
		print(self.frames)
		for level, tick in self.frames:
			if level == 0:
				if len(sequence) == 0:
					sequence.append(0)
					first_tick = tick
				else:
					diff = tick - first_tick
					if diff < 0:
						diff = (4294967295 - last_tick) + tick
					sequence.append(diff)

		# Analyze the frequency.
		sum_value = 0
		num_samples = 0
		last = 0
		print(len(sequence))
		for entry in sequence:
			if entry == 0:
				continue

			diff = entry - last
			last = entry
			if diff > 100 or diff < 10:
				continue

			sum_value += diff
			num_samples += 1


		if num_samples == 0:
			print("Unable to find the frequency of the signal")
			return

		period = sum_value / num_samples
		self.frequency = 1000000/period
                # Allow 15% deviation from average period
		approximate_period = period * 1.15
		print(approximate_period)
		return 1

	def _analyse_ir_pulses(self):
		print("Analyse called")
		m = self._decode_ir_sequence()
		self.frames = list()
		if m == 1:
                        return 1

	def enable(self):
		if self.pin_callback != None:
			return

		self.frames = list()
		self.pin_callback = self.pi.callback(self._sensor_pin, pigpio.EITHER_EDGE,self._pin_callback_entry)


	def disable(self):
		if self.pin_callback == None:
			return

		self.pi.set_watchdog(self._sensor_pin, 0)
		self.pin_callback.cancel()
		self.pin_callback = None

	def freq(self):
		return self.frequency

	def freq_calculator(self):
		system("sudo pigpiod")
		while(1):
			print('started')
			i=0
			pi = pigpio.pi()
			pin = 4
			self.init(pi,pin)
			self.enable()
			a = self._analyse_ir_pulses()
			pi.stop()
			while(i<=30000):
				i=i+1

			if a == 1:
				result = self.freq()
				print(result)
				return result
				break






