'''

mutation class

this should contain code that will mutate a file....
smart mutations:
	it should understand the structure of the file with hachori...
	it should do smart binary modification of ints...
	it should do smart string modification of ascii and unicode data...

dumb mutations:
	it should do a sliding window binary replace...
	it should do a sliding window binary mangle...
	it should do a rand size / rand data / rand number of mutations...

it should keep track of the progress of the mutations...
it should keep a copy of the un-mutated file...

TODO list all mutation methods as a class variable
TODO write all the dumb mutations 


'''
import time
import random
import re

from logger import Log

vals = [
"\x00","\x01","\x02","\x03","\x04","\x05","\x06","\x07","\x08","\x09","\x0a","\x0b","\x0c","\x0d","\x0e","\x0f",
"\x10","\x11","\x12","\x13","\x14","\x15","\x16","\x17","\x18","\x19","\x1a","\x1b","\x1c","\x1d","\x1e","\x1f",
"\x20","\x21","\x22","\x23","\x24","\x25","\x26","\x27","\x28","\x29","\x2a","\x2b","\x2c","\x2d","\x2e","\x2f",
"\x30","\x31","\x32","\x33","\x34","\x35","\x36","\x37","\x38","\x39","\x3a","\x3b","\x3c","\x3d","\x3e","\x3f",
"\x40","\x41","\x42","\x43","\x44","\x45","\x46","\x47","\x48","\x49","\x4a","\x4b","\x4c","\x4d","\x4e","\x4f",
"\x50","\x51","\x52","\x53","\x54","\x55","\x56","\x57","\x58","\x59","\x5a","\x5b","\x5c","\x5d","\x5e","\x5f",
"\x60","\x61","\x62","\x63","\x64","\x65","\x66","\x67","\x68","\x69","\x6a","\x6b","\x6c","\x6d","\x6e","\x6f",
"\x70","\x71","\x72","\x73","\x74","\x75","\x76","\x77","\x78","\x79","\x7a","\x7b","\x7c","\x7d","\x7e","\x7f",
"\x80","\x81","\x82","\x83","\x84","\x85","\x86","\x87","\x88","\x89","\x8a","\x8b","\x8c","\x8d","\x8e","\x8f",
"\x90","\x91","\x92","\x93","\x94","\x95","\x96","\x97","\x98","\x99","\x9a","\x9b","\x9c","\x9d","\x9e","\x9f",
"\xa0","\xa1","\xa2","\xa3","\xa4","\xa5","\xa6","\xa7","\xa8","\xa9","\xaa","\xab","\xac","\xad","\xae","\xaf",
"\xb0","\xb1","\xb2","\xb3","\xb4","\xb5","\xb6","\xb7","\xb8","\xb9","\xba","\xbb","\xbc","\xbd","\xbe","\xbf",
"\xc0","\xc1","\xc2","\xc3","\xc4","\xc5","\xc6","\xc7","\xc8","\xc9","\xca","\xcb","\xcc","\xcd","\xcd","\xcf",
"\xd0","\xd1","\xd2","\xd3","\xd4","\xd5","\xd6","\xd7","\xd8","\xd9","\xda","\xdb","\xdc","\xdd","\xde","\xdf",
"\xe0","\xe1","\xe2","\xe3","\xe4","\xe5","\xe6","\xe7","\xe8","\xe9","\xea","\xeb","\xec","\xed","\xee","\xef",
"\xf0","\xf1","\xf2","\xf3","\xf4","\xf5","\xf6","\xf7","\xf8","\xf9","\xfa","\xfb","\xfc","\xfd","\xfe","\xff"]

ITER = 0


class Mutator():
	def __init__(self, fuzz_loop, data, fuzz_file = None, thread_id = None, pre_callback = None, post_callback = None):
		self.data = data
		self.current_mutation = None
		self.fuzz_loop = fuzz_loop
		self.pre_callback = pre_callback
		self.post_callback = post_callback
		self.chunks = [4,8,16,32,64,128,256,512]
		self.string_mutations = None
		self.thread_id = thread_id
		self.fuzz_file = fuzz_file
		self.l = None


	def get_string_mutations(self):
		strings = ["","/.:/" + "A" * 5000 + "\x00\x00","/.../" + "A" * 5000 + "\x00\x00","/" + ".../" * 10, "/" + "../" * 12 + "etc/passwd","/" + "../" * 12 + "boot.ini","..:" * 13,"\\\\*","\\\\?\\","/\\" * 5000,"//." * 5000,"!@#$%%^#$%#$%@#$%$$@#$%^^**(()","%01%02%03@%04%0a%0d%0aASDF",	"//%00//","%00//","%00","%u0000","\x25\xfe\xf0\x25\x00\xff","\x25\xfe\xf0\x25\x01\xff" * 20,"%n" * 100,"%n" * 500,'"%n"' * 500,"%s" * 100,"%s" * 500,'"%s"' * 500,"touch tmp",";touch tmp;","notepad",";notepad;","\x0anotepad\x0a","1;SELECT%20*","'sqlattempt1","(sqlattempt2)","OR%201=1","\xDE\xAD\xBE\xEF","\xDE\xAD\xBE\xEF" * 10,"\xDE\xAD\xBE\xEF" * 100,"\xDE\xAD\xBE\xEF" * 1000,"\xDE\xAD\xBE\xEF" * 10000,"\x00" * 1000,"\x0d\x0a" * 100,"<>" * 500,]
		sizes = [127,128,255,256,257,511,512,513,1023,1024,1025,2048,2049,4096,4097,5000,10000,32762,32763,32764,32765,32766,32767,32768,32769,65533,65534,65535,65536,65537,99999,100000,500000,1000000]
		chars = ["A","B","1","2","3","<",">","'",'"',"/","\\","?","=","a=","&",",","(",")","]","[","%","*","-","+","{","}","\x14","\xfe","\xff",]
		for c in chars:
			for s in sizes:
				strings.append(c*s)
		strings.append("B"*64 + "\x00" + "B"*64)
		strings.append("B"*128 + "\x00" + "B"*128)
		strings.append("B"*512 + "\x00" + "B"*512)
		strings.append("B"*1024 + "\x00" + "B"*1024)
		strings.append("B"*2048 + "\x00" + "B"*2048)
		strings.append("B"*16384 + "\x00" + "B"*16384)
		strings.append("B"*32768 + "\x00" + "B"*32768)
		strings.append("SERVER"*2)
		strings.append("SERVER"*10)
		strings.append("SERVER"*100)
		strings.append("SERVER"*2 + "\xfe")
		strings.append("SERVER"*10 + "\xfe")
		strings.append("SERVER"*100 + "\xfe")
		self.string_mutations = strings
		

	def test_mutation(self, start=0, stop=0):
		count = 0
		while count <= 5:
			print "[%s] Iteration: %d" % (self.thread_id, count)
			time.sleep(random.randint(0, 10))
			count += 1
		return
#		for c in self.data:
#			for v in vals:
#				self.current_mutation = self.data.replace(c,v)
#				if self.thread_id:
#					print "[%s] Iteration: %d" % (self.thread_id, count)
#				else:
#					print "Iteration: %d" % (count)
#				self.fuzz_loop(self.current_mutation, 10)
#				count +=1
				
	def bit_flip(self, start=0, stop=0):
		count = 0

		if stop == 0:
			stop = len(self.data)
		
		for i in xrange(start/256, stop/256):
			for v in vals:
				part1 = self.data[0:i+1]
				part1 = part1[0:i]
				part1 += v
				part2 = self.data[i+1:len(self.data)]
				self.current_mutation = part1+part2
				if self.thread_id:
					print "[%s] Iteration: %d" % (self.thread_id, count)
				else:
					print "Iteration: %d" % (count)
				self.fuzz_loop(self.current_mutation, 10)
				self.l.log("%d\n" % count)
				count += 1
		return


	def window_replace(self, start=0):
		count = 0
		if start > 0:
			print "Skipping to Iteration: ", start
		for chunk in self.chunks:
			for i in xrange(chunk, len(self.data), chunk):
				part1 = self.data[0:i-chunk]
				part2 = self.data[i-chunk:i]
				part3 = self.data[i:len(self.data)]
				for val in vals:
					if part2.find(val) > -1:
						for v in vals:
							tmp = part2.replace(val, v)
							self.current_mutation = part1+tmp+part3
							if count >= start:
								if self.thread_id:
									print "[%s] Iteration: %d, Chunk Size: %d" % (self.thread_id, count, chunk)
								else:
									print "Iteration: %d, Chunk Size: %d" % (count, chunk)
								self.fuzz_loop(self.current_mutation, 10)
								self.l.log("%d\n" % count)
							count += 1
		return


	def rand_mutation(self, start=0, stop=0):
		max_rand_size = 10
		max_rand_mutations = 10
		count = 0
		if stop == 0:
			stop = len(self.data)
		while count < (stop-start):
			mutations = []
			for i in range(0, num_mutations):
				tmp = ""
			for sz in range(0, random.randint(1, max_rand_size)):
				tmp += chr(random.randint(0,255))
			mutations.append(tmp)
			fuzzed = self.data
			for mut in mutations:
				idx = random.randint(0, len(string))
				self.current_mutation = fuzzed[0:idx]+mut+fuzzed[idx+len(mut):]
			if self.thread_id:
				print "[%s] Iteration: %d" % (self.thread_id, count)
			else:
				print "Iteration: %d" % (count)
			self.fuzz_loop(self.current_mutation, 10)
			self.l.log("%d\n" % count)
			count += 1
		return


	def ascii_string_replace(self, start=0, stop=0):
		chars = r"A-Za-z0-9/\-:.,_$%'()[\]<> "
		shortest_run = 4
		regexp = '[%s]{%d,}' % (chars, shortest_run)
		pattern = re.compile(regexp)
		count = 0
		tmp = pattern.finditer(self.data)
		if stop == 0:
			stop = (len(pattern.findall(self.data)) * len(self.string_mutations)) * 2
		for string in tmp:
			for val in xrange(0, len(self.string_mutations)):
				count += 1 
				if count >= start/len(self.string_mutations) and count <= stop/len(self.string_mutations):
					self.current_mutation = self.data[0:string.start()]
					self.current_mutation += self.string_mutations[val][0:string.end()-string.start()]
					self.current_mutation += self.data[string.end():]
					self.fuzz_loop(self.current_mutation, 10)
					self.l.log("%d\n" % count)
		for string in tmp:
			for val in xrange(0, len(self.string_mutations)):
				count += 1
				if count >= start/len(self.string_mutations) and count <= stop/len(self.string_mutations):
					self.current_mutation = self.data[0:string.start()]
					self.current_mutation += self.string_mutations[val]
					self.current_mutation += self.data[len(self.string_mutations[val])+string.start():]
					self.fuzz_loop(self.current_mutation, 10)
					self.l.log("%d\n" % count)
		return


	def ascii_string_truncation(self, start=0, stop=0):
		#add up to dword to end of string
		#remove up to dword from end of string
		print "Not Implemented"
		return 

	def unicode_string_replace(self, start=0, stop=0):
		print "Not Implemented"
		return

	def unicode_string_truncation(self, start=0, stop=0):
		print "Not Implemented"
		return

	def binary_interger_bounding(self, start=0, stop=0):
		#for dword in file
		#if dword not ascii
		#fuzz 
		#repeat with word
		print "Not Implemented"
		return
	
	def binary_swap(self, start=0, stop=0):
		#for dword in file
		#change endian ness
		#repeat with word
		print "Not Implemented"
		return


	def get_max_mutations(self, mutation_function):
		if mutation_function == "test_mutation":
			return (len(self.data) * 256) / 25
		if mutation_function == "bit_flip":
			return len(self.data) * 256
		if mutation_function == "window_replace":
			return 1
		if mutation_function == "rand_mutation":
			return len(self.data) * 32
		if mutation_function == "ascii_string_replace":
			chars = r"A-Za-z0-9/\-:.,_$%'()[\]<> "
			shortest_run = 4
			regexp = '[%s]{%d,}' % (chars, shortest_run)
			pattern = re.compile(regexp)
			self.get_string_mutations()
			return (len(pattern.findall(self.data)) * len(self.string_mutations)) * 2
		return -1


	def run(self, mutation_function, start = 0, stop = 0):

		self.l = Log(mutation_function, self.fuzz_file)
		last = self.l.get_last()
		if len(last) > 1:
			start = int(last)		
			
		if mutation_function == "test_mutation":

			if start == stop:
				self.test_mutation()
			else:
				self.test_mutation(start, stop)

		if mutation_function == "bit_flip":
			if start == stop:
				self.bit_flip()
			else:
				self.bit_flip(start, stop)

		if mutation_function == "window_replace":
			self.window_replace(start)

		if mutation_function == "rand_mutation":
			if start == stop:
				self.rand_mutation()
			else:
				self.rand_mutation(start, stop)

		if mutation_function == "ascii_string_replace":
			if start == stop:
				self.strings()
			else:
				self.strings(start, stop)
		self.l.remove()
		return	
		



'''
test functions...
'''

def test_callback(data, timeout):
	global ITER
	#print "test_callback"
	fd = open("%d.ogg" % ITER, "wb")
	fd.write(data)
	fd.close()
	ITER += 1


def pre(data):
	print "pre"

def post(data):
	print "post"

if __name__ == "__main__":

	file = open("/home/udev/android-sdk-linux/platform-tools/fuzz/corpus/ogg/htc_bug.ogg", "rb")
	data = file.read()
	file.close()

	mut = Mutator(test_callback, data, None, pre, post)
	max_mut = mut.get_max_mutations("ascii_string_replace")

	emus = 8
	tmp = []
	for i in range(0, emus):
		print "i", i
		print "max_mut", max_mut
		print "max_mut / emus", max_mut / emus
		print "(max_mut/emus) * i", (max_mut/emus) * i
		tmp.append((max_mut/emus) * i)
	if len(tmp) % 2 != 0:
		tmp.append(max_mut)
	print tmp
	for i in range(0, len(tmp)-1):
		mut.run("strings", tmp[i], tmp[i+1])



	
	
	





