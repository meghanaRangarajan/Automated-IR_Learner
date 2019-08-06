import pigpio
import asyncio
import functools
import const
import RPi.GPIO as gpio
import time
from os import system
from clean_buffer import *

class necd:
	def __init__(self):
		self.callback = None
		self.pin_callback = None
		self.frames = list()
		self._sensor_pin = None
		self.protocol = list()
		self.protocol_id = None
		self.result = None
		self.previous = None
		self.sequence = list()
		self.summary = list()
		self.differences = list()

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
			if len(self.sequence) < 5:
				# Short sequence. Discard
				print("Discarding Short Sequence")
				self.pi.set_watchdog(self._sensor_pin, 0)
				self.sequence = list()
				self.summary = list()
				self.differences = list()
				return
			# Watchdog expired.
			self.loop.call_soon_threadsafe(functools.partial(self._analyse_ir_pulses))
			self.disable()
			return

		if len(self.sequence) == 0:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)
		if len(self.sequence) == 1:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)

		self.apply(level,tick)

		


	def _try_decode_nec(self, s):
		summary = list()
		sequence = clean(s)
		print("decoding NEC")
		start  = 0
		header = False
		result = 0
		self.protocol_id = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.NEC_HEADER_MARK * 0.95 and sequence[i][1] < const.NEC_HEADER_MARK * 1.05
			if (ns) and sequence[i][0]==1:
				start  = i
				break

		if(sequence[start+1][1] > const.NEC_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.NEC_HEADER_SPACE * 1.05)and sequence[start+1][0]==0:
			header = True
			start = start+1

		if header == False:
                        return None

		for i in range(len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.NEC_HIGH_SPACE*2):
					end = i

		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.NEC_MARK * 0.90 and info < const.NEC_MARK * 1.10):
					info = const.NEC_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.NEC_HIGH_SPACE * 2):
					
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary)==0:
                        return None
		print(summary)
		if summary[(len(summary))-1][0]==1:
			summary.pop()

		if len(summary)<2:
			return None

		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.NEC_MARK * 0.90 and mark < const.NEC_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.NEC_LOW_SPACE * 0.90 and space < const.NEC_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.NEC_HIGH_SPACE * 0.90 and space < const.NEC_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result


	def _try_decode_rc5(self, s):
                print("Testing for RC5")
                self.protocol_id = 1
                i=0
                x=0
                s = clean(s)
                for m in range(len(s)):
                        if(s[m][1] > const.RC5_SLICE * 0.90 and s[m][1] < const.RC5_SLICE * 1.10):
                                i+=1
                        elif (s[m][1] > const.RC5_SLICE_ * 0.90 and s[m][1] < const.RC5_SLICE_ * 1.10):
                                i+=2
                        else:
                                x=(m)
                                break

                k = list()

                for m in range(0,x):
                        if(s[m][1] > const.RC5_SLICE * 0.90 and s[m][1] < const.RC5_SLICE * 1.10):
                                k.append(32)
                        elif (s[m][1] > const.RC5_SLICE_ * 0.90 and s[m][1] < const.RC5_SLICE_ * 1.10):
                                k.append(64)
                                k.append(64)


                result=0
                change=0
                print(k)
                for i in range(0,len(k),2):
                        mark = k[i]
                        if mark==64:
                                if change==0:
                                        result <<= 1
                                        result |= 1
                                        change=1
                                elif change==1:
                                        result <<= 1
                                        change=0
                        elif mark==32:
                                if change==0:
                                        result <<= 1
                                        change=0
                                elif change==1:
                                        result <<= 1
                                        result |= 1
                                        change=1

                result>>=1
                print(hex(result))

                if result == None or result == 0:
                        return None
                return result

	def _try_decode_rc6(self, s):
		print("Testing for RC6")
		self.protocol_id = 2
		i=0
		x=0
		for m in range(len(s)):
			if(s[m][1] > const.RC6_SLICE * 0.90 and s[m][1] < const.RC6_SLICE * 1.10):
				i+=1
			elif (s[m][1] > const.RC6_SLICE_ * 0.90 and s[m][1] < const.RC6_SLICE_ * 1.10):
				i+=2
			else:
				x=(m)
				break

		k = list()

		for m in range(0,x):
			if(s[m][1] > const.RC6_SLICE * 0.90 and s[m][1] < const.RC6_SLICE * 1.10):
				k.append(32)
			elif (s[m][1] > const.RC6_SLICE_ * 0.90 and s[m][1] < const.RC6_SLICE_ * 1.10):
				k.append(64)
				k.append(64)


		result=0
		change=0
		print(k)
		for i in range(0,len(k),2):
			mark = k[i]
			if mark==64:
				if change==1:
					result <<= 1
					result |= 1
					change=0
				elif change==0:
					result <<= 1
					change=1
			elif mark==32:
				if change==1:
					result <<= 1
					change=1
				elif change==0:
					result <<= 1
					result |= 1
					change=0

		if result == None or result == 0:
			return None
		return result

	def _try_decode_rcmm(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for RCMM")
		self.protocol_id = 3

		if not (header_mark > const.RCMM_HEADER_MARK * 0.90 and header_mark < const.RCMM_HEADER_MARK * 1.10):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.RCMM_HEADER_SPACE * 0.90 and header_space < const.RCMM_HEADER_SPACE * 1.15):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.RCMM_SPACE3 * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.RCMM_MARK * 0.90 and mark < const.RCMM_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.RCMM_SPACE0 * 0.90 and space < const.RCMM_SPACE0 * 1.10):
				result <<= 1
				result <<= 1

			elif (space > const.RCMM_SPACE1 * 0.90 and space < const.RCMM_SPACE1 * 1.10):
				result <<= 1
				result <<= 1
				result |= 1

			elif (space > const.RCMM_SPACE2 * 0.90 and space < const.RCMM_SPACE2 * 1.10):
				result <<= 1
				result |= 1
				result <<= 1

			elif (space > const.RCMM_SPACE3 * 0.90 and space < const.RCMM_SPACE3 * 1.10):
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			else:
				# Bad decode.
				
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_xmp1(self, sequence):
		self.protocol_id = 4
		result = 0
		print("testing for XMP1")
		for i in range(0, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.XMP1_SPACE15 * 2 or space>const.XMP1_GAP:
				print("Space greater than HIGH_SPACE detected")
				break

			if i%16 is 0 and i is not 0:
				continue


			if not (mark > const.XMP1_MARK * 0.90 and mark < const.XMP1_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.XMP1_SPACE0 * 0.90 and space < const.XMP1_SPACE0 * 1.10):

				result <<= 1
				result <<= 1
				result <<= 1
				result <<= 1

			elif (space > const.XMP1_SPACE1 * 0.90 and space < const.XMP1_SPACE1 * 1.10):

				result <<= 1
				result <<= 1
				result <<= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE2 * 0.90 and space < const.XMP1_SPACE2 * 1.10):

				result <<= 1
				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1


			elif (space > const.XMP1_SPACE3 * 0.90 and space < const.XMP1_SPACE3 * 1.10):

				result <<= 1
				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE4 * 0.90 and space < const.XMP1_SPACE4 * 1.10):

				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1

			elif (space > const.XMP1_SPACE5 * 0.90 and space < const.XMP1_SPACE5 * 1.10):

				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE6 * 0.90 and space < const.XMP1_SPACE6 * 1.10):

				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1

			elif (space > const.XMP1_SPACE7 * 0.90 and space < const.XMP1_SPACE7 * 1.10):

				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE8 * 0.90 and space < const.XMP1_SPACE8 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result <<= 1

			elif (space > const.XMP1_SPACE9 * 0.90 and space < const.XMP1_SPACE9 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE10 * 0.90 and space < const.XMP1_SPACE10 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1

			elif (space > const.XMP1_SPACE11 * 0.90 and space < const.XMP1_SPACE11 * 1.10):
				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE12 * 0.90 and space < const.XMP1_SPACE12 * 1.10):
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1

			elif (space > const.XMP1_SPACE13 * 0.90 and space < const.XMP1_SPACE13 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result <<= 1
				result |= 1

			elif (space > const.XMP1_SPACE14 * 0.90 and space < const.XMP1_SPACE14 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1

			elif (space > const.XMP1_SPACE15 * 0.90 and space < const.XMP1_SPACE15 * 1.10):

				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			else:
				# Bad decode.
				
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_rc5_57(self, s):
                print("Testing for RC5_57")
                self.protocol_id = 5
                s = clean(s)
                i=0
                x=0
                start = 0
                for m in range(0,len(s)):
                        if (s[m][1] > const.RC5_57_SLICE_ * 2):
                                start = m
                                break
                print(start,"   ",s[start][1])
                for m in range((start+1),len(s)):
                        if(s[m][1] > const.RC5_57_SLICE * 0.80 and s[m][1] < const.RC5_57_SLICE * 1.20):
                                i+=1
                        elif (s[m][1] > const.RC5_57_SLICE_ * 0.80 and s[m][1] < const.RC5_57_SLICE_ * 1.20):
                                i+=2
                        else:
                                x=(m)
                                break

                print(x,"   ",s[x][1])
                k = list()

                for m in range(start+1,x):
                        if(s[m][1] > const.RC5_57_SLICE * 0.80 and s[m][1] < const.RC5_57_SLICE * 1.20):
                                k.append(52)
                        elif (s[m][1] > const.RC5_57_SLICE_ * 0.80 and s[m][1] < const.RC5_57_SLICE_ * 1.20):
                                k.append(104)
                                k.append(104)


                result=0
                change=0
                print(k)
                for i in range(0,len(k),2):
                        mark = k[i]
                        if mark==104:
                                if change==0:
                                        result <<= 1
                                        result |= 1
                                        change=1
                                elif change==1:
                                        result <<= 1
                                        change=0
                        elif mark==52:
                                if change==0:
                                        result <<= 1
                                        change=0
                                elif change==1:
                                        result <<= 1
                                        result |= 1
                                        change=1

                result>>=1
                print(hex(result))

                if result == None or result == 0:
                        return None
                return result


	def _try_decode_nec_short(self, s):
		summary = list()
		print("decoding NEC SHORT")
		sequence = clean(s)
		start  = 0
		self.protocol_id = 6
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.NEC_SHORT_HEADER_MARK * 0.95 and sequence[i][1] < const.NEC_SHORT_HEADER_MARK * 1.05
			if (ns) and sequence[i][0]==1:
				start  = i
				break
			else:
                                continue

		if(sequence[start+1][1] > const.NEC_SHORT_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.NEC_SHORT_HEADER_SPACE * 1.05) and sequence[start+1][0]==0:
			header = True
			start = start+1

		print(start,"  ",)
		if header == False:
                        return None
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.NEC_SHORT_HIGH_SPACE*3):
					end = i
					print(i)
					break
		print(end)
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.NEC_SHORT_MARK * 0.90 and info < const.NEC_SHORT_MARK * 1.10):
					info = const.NEC_SHORT_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.NEC_SHORT_HIGH_SPACE * 2):
					
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.NEC_SHORT_MARK * 0.90 and mark < const.NEC_SHORT_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.NEC_SHORT_LOW_SPACE * 0.90 and space < const.NEC_SHORT_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.NEC_SHORT_HIGH_SPACE * 0.90 and space < const.NEC_SHORT_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))

		if result == None or result == 0:
			return None
		return result

	def _try_decode_sony(self, s):
                print("decoding SONY")
                sequence = clean(s)
                self.protocol_id = 7
                summary = list()
                start  = 0
                header = False
                result = 0
                end = 0
                for i in range(len(sequence)):
                    ns = sequence[i][1] > const.SONY_HEADER_MARK * 0.95 and sequence[i][1] < const.SONY_HEADER_MARK * 1.05
                    if (ns) and sequence[i][0]==1:
                            start  = i
                            break

                if(sequence[start+1][1] > const.SONY_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.SONY_HEADER_SPACE * 1.05) and sequence[start+1][0]==0:
                    header = True
                    start = start+1

                if header == False:
                        return None

                print(start,"   ",sequence[start][1])
                for i in range(start,len(sequence)):
                    if(sequence[i][0]==0):
                            if((sequence[i][1] > const.SONY_HEADER_SPACE*2) and sequence[i][0]==0):
                                    end = i
                                    print(i)
                                    break
                print(end,"   ",sequence[end][1])
                for i in range((start+1),(end-1)):
                    if(sequence[i][0] == 0):
                            info = sequence[i][1]
                            if not (info > const.SONY_SPACE * 0.90 and info < const.SONY_SPACE * 1.10):
                                    info = const.SONY_SPACE
                    if(sequence[i][0] == 1):
                            info = sequence[i][1]
                    summary.append((sequence[i][0],info))

                print("______________in decode_______________")
                print(len(summary))
                if len(summary) == 0 or len(summary) == 1:
                    return None
                print(summary)
                if summary[len(summary) -1][0]==1:
                    summary.pop()


                for i in range(0, len(summary), 2):
                    mark = summary[i][1]
                    space = summary[i + 1][1]

                    if not (space > const.SONY_SPACE * 0.90 and space < const.SONY_SPACE * 1.10):
                            # Bad decode
                            print("Bad space Detected")
                            print(mark)
                            result = 0
                            break

                    if (mark > const.SONY_LOW_MARK * 0.90 and mark < const.SONY_LOW_MARK * 1.10):
                            result <<= 1
                    elif (mark > const.SONY_HIGH_MARK * 0.90 and mark < const.SONY_HIGH_MARK * 1.10):
                            result <<= 1
                            result |= 1
                    else:
                            # Bad decode.
                            
                            print(space)
                            result = 0
                            break

                result<<=1
                print(hex(result))
                if result == None or result == 0:
                    return None
                return result


	def _try_decode_panasonic(self, s):
		print("decoding panasonic")
		sequence = clean(s)
		self.protocol_id = 8
		summary = list()

		start  = 0
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.PANA_HEADER_MARK * 0.95 and sequence[i][1] < const.PANA_HEADER_MARK * 1.05
			if (ns):
				start  = i
				break

		if(sequence[start+1][1] > const.PANA_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.PANA_HEADER_SPACE * 1.05):
			header = True
			start = start+1

		print(start)
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.PANA_HIGH_SPACE*3):
					end = i
					print(i)
					break
		print(end)
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.PANA_MARK * 0.90 and info < const.PANA_MARK * 1.10):
					info = const.PANA_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.PANA_HIGH_SPACE * 2):
					
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.PANA_MARK * 0.90 and mark < const.PANA_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.PANA_LOW_SPACE * 0.90 and space < const.PANA_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.PANA_HIGH_SPACE * 0.90 and space < const.PANA_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result

	def _try_decode_jvc(self, s):
		print("decoding JVC")
		sequence = clean(s)
		self.protocol_id = 9
		summary = list()
		start  = 0
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.JVC_HEADER_MARK * 0.95 and sequence[i][1] < const.JVC_HEADER_MARK * 1.05
			if (ns):
				start  = i
				break

		if(sequence[start+1][1] > const.JVC_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.JVC_HEADER_SPACE * 1.05):
			header = True
			start = start+1

		print(start)
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.JVC_HIGH_SPACE*3):
					end = i
					print(i)
					break
		print(end)
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.JVC_MARK * 0.90 and info < const.JVC_MARK * 1.10):
					info = const.JVC_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.JVC_HIGH_SPACE * 2):
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.JVC_MARK * 0.90 and mark < const.JVC_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.JVC_LOW_SPACE * 0.90 and space < const.JVC_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.JVC_HIGH_SPACE * 0.90 and space < const.JVC_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result

	def _try_decode_rc5_38(self, s):
                print("Testing for RC5_38")
                self.protocol_id =10
                s = clean(s)
                i=0
                x=0
                start = 0
                for m in range(0,len(s)):
                        if (s[m][1] > const.RC5_38_SLICE_ * 2):
                                start = m
                                break
                print(start,"   ",s[start][1])
                for m in range((start+1),len(s)):
                        if(s[m][1] > const.RC5_38_SLICE * 0.80 and s[m][1] < const.RC5_38_SLICE * 1.20):
                                i+=1
                        elif (s[m][1] > const.RC5_38_SLICE_ * 0.80 and s[m][1] < const.RC5_38_SLICE_ * 1.20):
                                i+=2
                        else:
                                x=(m)
                                break

                print(x,"   ",s[x][1])
                k = list()

                for m in range(start+1,x):
                        if(s[m][1] > const.RC5_38_SLICE * 0.80 and s[m][1] < const.RC5_38_SLICE * 1.20):
                                k.append(32)
                        elif (s[m][1] > const.RC5_38_SLICE_ * 0.80 and s[m][1] < const.RC5_38_SLICE_ * 1.20):
                                k.append(64)
                                k.append(64)


                result=0
                change=0
                print(k)
                for i in range(0,len(k),2):
                        mark = k[i]
                        if mark==64:
                                if change==0:
                                        result <<= 1
                                        result |= 1
                                        change=1
                                elif change==1:
                                        result <<= 1
                                        change=0
                        elif mark==32:
                                if change==0:
                                        result <<= 1
                                        change=0
                                elif change==1:
                                        result <<= 1
                                        result |= 1
                                        change=1

                print(hex(result))
                result>>=1

                if result == None or result == 0:
                        return None
                return result
        
	def _try_decode_sharp(self, s):
		result = 0
		end = 0
		summary = list()
		self.protocol_id = 11
		sequence = clean(s)
		print("Testing for SHARP")
		for i in range(len(sequence)):
			ns = (sequence[i][1] > const.SHARP_HIGH_SPACE* 2) and not sequence[i][1] > const.SHARP_GAP_SPACE * 0.90 and sequence[i][1] < const.SHARP_GAP_SPACE * 1.10
			if (ns):
				start  = i
				break
		for i in range(start+1,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1] > const.SHARP_HIGH_SPACE* 2) and not(sequence[i][1] > const.SHARP_GAP_SPACE * 0.90 and sequence[i][1] < const.SHARP_GAP_SPACE * 1.10):
					end = i
					print(i)
					break
		print(start,"  ",sequence[start][1])
		print(end,"  ",sequence[end][1])
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.SHARP_MARK * 0.90 and info < const.SHARP_MARK * 1.10):
					info = const.SHARP_MARK
			if sequence[i][0] == 0:
				info = sequence[i][1]
				if (sequence[i][1] > const.SHARP_GAP_SPACE * 0.90 and sequence[i][1] < const.SHARP_GAP_SPACE * 1.10):
                                        summary.pop()
                                        continue                                        
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
			return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.SHARP_MARK * 0.90 and mark < const.SHARP_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.SHARP_LOW_SPACE * 0.90 and space < const.SHARP_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.SHARP_HIGH_SPACE * 0.90 and space < const.SHARP_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result

	def _try_decode_rca_38(self, s):
		print("decoding RCA_38")
		sequence = clean(s)
		self.protocol_id = 12
		summary = list()
		start  = 0
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.RCA38_HEADER_MARK * 0.95 and sequence[i][1] < const.RCA38_HEADER_MARK * 1.05
			if (ns):
				start  = i
				break

		if(sequence[start+1][1] > const.RCA38_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.RCA38_HEADER_SPACE * 1.05):
			header = True
			start = start+1

		print(start)
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.RCA38_HIGH_SPACE*3):
					end = i
					print(i)
					break
		print(end)
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.RCA38_MARK * 0.90 and info < const.RCA38_MARK * 1.10):
					info = const.RCA38_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.RCA38_HIGH_SPACE * 2):
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.RCA38_MARK * 0.90 and mark < const.RCA38_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.RCA38_LOW_SPACE * 0.90 and space < const.RCA38_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.RCA38_HIGH_SPACE * 0.90 and space < const.RCA38_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result

	def _try_decode_rca_57(self, s):
		print("decoding RCA_57")
		sequence = clean(s)
		self.protocol_id = 13
		summary = list()
		start  = 0
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.RCA57_HEADER_MARK * 0.90 and sequence[i][1] < const.RCA57_HEADER_MARK * 1.10
			if (ns) and sequence[i][0]==1 :
				start  = i
				break
		print(start,"   ",sequence[start][1])
		print(start+1,"   ",sequence[start+1][1])

		if(sequence[start+1][1] > const.RCA57_HEADER_SPACE * 0.90 and sequence[start+1][1] < const.RCA57_HEADER_SPACE * 1.10) and sequence[start+1][0]==0:
			header = True
			start = start+1

		print(start,"   ",sequence[start][1])
		if header == False:
                        print("no header")
                        return None
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.RCA57_HIGH_SPACE*3):
					end = i
					break
		print(end,"   ",sequence[end][1])
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.RCA57_MARK * 0.90 and info < const.RCA57_MARK * 1.10):
					info = const.RCA57_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.RCA57_HIGH_SPACE * 2):
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.RCA57_MARK * 0.90 and mark < const.RCA57_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.RCA57_LOW_SPACE * 0.90 and space < const.RCA57_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.RCA57_HIGH_SPACE * 0.90 and space < const.RCA57_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result


	def _try_decode_mitsubishi(self, s):
		print("decoding MITSUBISHI")
		sequence = clean(s)
		self.protocol_id = 14
		summary = list()
		start  = 0
		header = False
		result = 0
		end = 0
		for i in range(len(sequence)):
			ns = sequence[i][1] > const.MITSUBISHI_HEADER_MARK * 0.95 and sequence[i][1] < const.MITSUBISHI_HEADER_MARK * 1.05
			if (ns):
				start  = i
				break

		if(sequence[start+1][1] > const.MITSUBISHI_HEADER_SPACE * 0.95 and sequence[start+1][1] < const.MITSUBISHI_HEADER_SPACE * 1.05):
			header = True
			start = start+1

		print(start)
		for i in range(start,len(sequence)):
			if(sequence[i][0]==0):
				if(sequence[i][1]>const.MITSUBISHI_HIGH_SPACE*3):
					end = i
					print(i)
					break
		print(end)
		for i in range((start+1),(end-1)):
			if(sequence[i][0] == 1):
				info = sequence[i][1]
				if not (info > const.MITSUBISHI_MARK * 0.90 and info < const.MITSUBISHI_MARK * 1.10):
					info = const.MITSUBISHI_MARK
			if(sequence[i][0] == 0):
				info = sequence[i][1]
				if (info > const.MITSUBISHI_HIGH_SPACE * 2):
					i+=2
					continue
			summary.append((sequence[i][0],info))

		print("______________in decode_______________")
		print(len(summary))
		if len(summary) == 0 or len(summary) == 1:
                        return None
		print(summary)
		if summary[len(summary) -1][0]==1:
			summary.pop()


		for i in range(0, len(summary), 2):
			mark = summary[i][1]
			space = summary[i + 1][1]

			if not (mark > const.MITSUBISHI_MARK * 0.90 and mark < const.MITSUBISHI_MARK * 1.10):
				# Bad decode
				print("Bad Mark Detected")
				print(mark)
				result = 0
				break

			if (space > const.MITSUBISHI_LOW_SPACE * 0.90 and space < const.MITSUBISHI_LOW_SPACE * 1.10):
				result <<= 1
			elif (space > const.MITSUBISHI_HIGH_SPACE * 0.90 and space < const.MITSUBISHI_HIGH_SPACE * 1.10):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				
				print(space)
				result = 0
				break

		print(hex(result))
		if result == None or result == 0:
			return None
		return result

	def _try_decode_konka(self, s):
                print("decoding KONKA")
                sequence = clean(s)
                self.protocol_id = 15
                summary = list()
                start  = 0
                header = False
                result = 0
                end = 0
                for i in range(len(sequence)):
                    ns = sequence[i][1] > const.KONKA_HEADER_MARK * 0.95 and sequence[i][1] < const.KONKA_HEADER_MARK * 1.05
                    if (ns) and sequence[i][0]==1:
                            start  = i
                            break

                if(sequence[start+1][1] > const.KONKA_HEADER_MARK * 0.95 and sequence[start+1][1] < const.KONKA_HEADER_MARK * 1.05) and sequence[start+1][0]==0:
                    header = True
                    start = start+1

                if header == False:
                        return None

                print(start,"   ",sequence[start][1])
                for i in range(start,len(sequence)):
                    if(sequence[i][0]==0):
                            if((sequence[i][1] > const.KONKA_TRAILER_SPACE * 0.90 and sequence[i][1] < const.KONKA_TRAILER_SPACE * 1.10) and sequence[i][0]==0):
                                    end = i
                                    print(i)
                                    break
                print(end,"   ",sequence[end][1])
                for i in range((start+1),(end-1)):
                    if(sequence[i][0] == 1):
                            info = sequence[i][1]
                            if not (info > const.KONKA_MARK * 0.90 and info < const.KONKA_MARK * 1.10):
                                    info = const.KONKA_MARK
                    if(sequence[i][0] == 0):
                            info = sequence[i][1]
                            if (info > const.KONKA_HIGH_SPACE * 2):
                                    i+=2
                                    continue
                    summary.append((sequence[i][0],info))

                print("______________in decode_______________")
                print(len(summary))
                if len(summary) == 0 or len(summary) == 1:
                    return None
                print(summary)
                if summary[len(summary) -1][0]==1:
                    summary.pop()


                for i in range(0, len(summary), 2):
                    mark = summary[i][1]
                    space = summary[i + 1][1]

                    if not (mark > const.KONKA_MARK * 0.90 and mark < const.KONKA_MARK * 1.10):
                            # Bad decode
                            print("Bad Mark Detected")
                            print(mark)
                            result = 0
                            break

                    if (space > const.KONKA_LOW_SPACE * 0.90 and space < const.KONKA_LOW_SPACE * 1.10):
                            result <<= 1
                    elif (space > const.KONKA_HIGH_SPACE * 0.90 and space < const.KONKA_HIGH_SPACE * 1.10):
                            result <<= 1
                            result |= 1
                    else:
                            # Bad decode.
                            
                            print(space)
                            result = 0
                            break

                print(hex(result))
                if result == None or result == 0:
                    return None
                return result



	def apply(self,level,tick):
		first_tick = 0
		if level == 0:
			if len(self.sequence) == 0:
				first_tick = tick
				self.sequence.append(0)
			else:
				diff = tick - first_tick
				if diff < 0:
					diff = (4294967295 - last_tick) + tick
				self.sequence.append(diff)
				if len(self.sequence)>2:
					self.differences.append(diff - self.sequence[(len(self.sequence)-2)])

	def _decode_ir_sequence(self,frequency):
		# Signal is active low. Hence the lead in is a -ve edge
		print("inside decode")
		#print("__________________________________________________sequence______________________________________________________________________")
		print("length of sequence = ",len(self.sequence))
		#print(self.sequence)
		print("_________________________________________________differences_____________________________________________________________________")
		print("length of differences = ",len(self.differences))
		#print(self.differences)
		period = 1000000/frequency
		approximate_period = period * 1.15
		approximate_period = approximate_period+1
		print("approximate_period = ",approximate_period)
		print("frequency",frequency)

		current = 1
		length = 0
		for i in self.differences:
			if i < approximate_period:
				if current == 1:
					# Tracking a mark. Just add the length
					length += i
				else:
					# Tracking a space. Switch to tracking mark
					length -= int(period)
					self.summary.append((0, length))
					length = i
					current = 1
			else:
				if current == 1:
					# Tracking a mark. Switch to tracking space
					length += int(period)
					self.summary.append((1, length))
					length = i
					current = 0
				else:
					length += i

		print("__________________________________________________summary______________________________________________________________________")
		print("length of summary = ",len(self.summary))
		self.summary = list(map(lambda x: (x[0], int(round(x[1] / period))), self.summary))
		print(self.summary)

		if len(self.summary)==0 or len(self.summary)==1:
			return 0

		if frequency>38000*0.97 and frequency <38000*1.03:
			self.result = self._try_decode_nec(self.summary)
			if self.result==0 or self.result==None:
				self.result = self._try_decode_nec_short(self.summary)
				if self.result==0 or self.result==None:
					self.result = self._try_decode_panasonic(self.summary)
					if self.result==0 or self.result==None:
						self.result = self._try_decode_jvc(self.summary)
						if self.result==0 or self.result==None:
                                                        self.result = self._try_decode_sharp(self.summary)
                                                        if self.result==0 or self.result==None:
                                                                self.result = self._try_decode_mitsubishi(self.summary)
                                                                if self.result==0 or self.result==None:
                                                                        self.result = self._try_decode_konka(self.summary)
                                                                        if self.result==0 or self.result==None:
                                                                                self.result = self._try_decode_rc5_38(self.summary)
                                                                                if self.result==0 or self.result==None:
                                                                                        self.result = self._try_decode_rca_38(self.summary)
		elif frequency>36000*0.80 and frequency <36000*1.05:
			self.result = self._try_decode_rcmm(self.summary)
			if self.result==0 or self.result==None:
				self.result = self._try_decode_rc5(self.summary)
				if self.result==0 or self.result==None:
                                        self.result = self._try_decode_rc6(self.summary)
				
		elif frequency>57000*0.80 and frequency <57000*1.20:
			self.result = self._try_decode_rc5_57(self.summary)
			if self.result==0 or self.result==None:
				self.result = self._try_decode_rca_57(self.summary)

		elif frequency>40000*0.80 and frequency <40000*1.20:
			self.result = self._try_decode_sony(self.summary)

		if self.callback is not None:
			self.callback(code)

		print(self.result)
		print(self.protocol_id)
		if(self.result == None or self.result == 0):
			return 0
		return 1

	def result_return(self):
		print("result is "+str(hex(self.result)))
		return self.result

	def _analyse_ir_pulses(self,frequency):
		print("Analyse called")
		m = self._decode_ir_sequence(frequency)
		self.sequence = list()
		self.summary = list()
		self.differences = list()
		if m ==1:
			return 1

	def enable(self):
		if self.pin_callback != None:
			print("pincallback  = none")
			return

		self.previous = 0
		self.sequence = list()
		self.summary = list()
		self.differences = list()
		print("inside enable")
		self.pin_callback = self.pi.callback(self._sensor_pin, pigpio.EITHER_EDGE,self._pin_callback_entry)
		print('done with enable')


	def disable(self):
		if self.pin_callback == None:
			return

		self.pi.set_watchdog(self._sensor_pin, 0)
		self.pin_callback.cancel()
		self.pin_callback = None

	def set_callback(self, callback):
		self.callback = callback

	def return_protcol_id(self):
		print(self.protocol_id)
		return self.protocol_id

	def decode(self):
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
				result = self.result_return()
				p_id = self.return_protcol_id()
				print(p_id)
				return result
				break




