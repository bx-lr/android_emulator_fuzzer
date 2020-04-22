'''
fuzz control 

start up specified number of emulator instances and versions

wait for all devices to come on line...
kick of a fuzzer thread for each adb device instance

fuzzer thread should do all of the good stuff

TODO make all the arguments taken from a config file
TODO create a sessions file that each thead will log mutation primitive, file, and iteration

TODO see if i can speed up the thread death...
TODO make variables out of the hard coded values (com.android.browser/.BrowserActivity, etc.)
TODO make self.mutation_method a list
TODO make this a class called from the fuzz driver
TODO create a crash log class

TODO set max mutations per function
TODO be able to split mutations per function across multiple emulator instances

TODO after a set # of iterations we should kill all processes associated with the fuzzing and delete the emulator then restart it
'''

from adb import ADB
from emulator import Emulator
from mutator import Mutator

import time
import threading
import os
import Queue
import signal
import sys
import random
import shutil

EMULATOR_PATH = "/home/udev/android-sdk-linux/tools/"
NUM_EMULATORS = 1
API_LEVEL = "android-15"
SDCARD = True

ADB_PATH = "/home/udev/android-sdk-linux/platform-tools/"
FUZZ_SAMPLE_DIR = "/home/udev/android-sdk-linux/platform-tools/fuzz/corpus/FIXME/"
CRASH_DIR = "/home/udev/android-sdk-linux/platform-tools/fuzz/crashes/"
MIMETYPE = "audio/mid"
MAX_ITERATION = 4096
#bit_flip window_replace
PRIMITIVES = ["window_replace"]

emu = Emulator(EMULATOR_PATH)
adb = ADB(ADB_PATH)

class FuzzThread(threading.Thread):
	def __init__(self, device, queue):
		threading.Thread.__init__(self)
		self.device = device
		self.queue = queue
		self.fuzz_file = None
		self.mutation_method = None
		self.fuzz_data = None
		self.mutation_stop = 0
		self.mutation_start = 0
		#restart emulator stuff
		#use self.device to get the process and args... kill it delete the emulator and use the args to restart
		self.max_iterations = 1000
		self.iteration_count = 0
		#not used right, yet
		self.time_to_die = False


	#not really working.... damn queue
	def die(self, msg):
		print msg
		self.queue.task_done()
		sys.exit(0)

	#need to do this when the emulator freaks...	
	def restart(self):
		#print "self.device=", self.device
		avd_name = emu.get_running_avd(self.device.split("\t")[0])
		#print "avd_name=", avd_name
		adb.stop_adb()
		adb.start_adb()
		while True:
			#if we do this to many times and we dont have the correct # of emulators
			#we need to kill and restart adb
			device_list = adb.check_devices()
			if type(device_list) == type(None):
				time.sleep(2)
				continue
		if self.device in device_list:
			#print "removing... ", self.device
			device_list.remove(self.device)
		args = emu.get_running_avd_args(avd_name).rstrip("\r\n")
		#print "args=", args
		print "restarting emulator:"
		print "\t", self.device
		print "\t", avd_name
		print "\t", args
		emu.kill_emulator(avd_name)
		emu.start_avd(avd_name, args)
		while (True):
			if adb.remount(self.device, "/mnt/sdcard"):
				break
			time.sleep(2)
		return 

	
	def update_fuzz_data(self):
		file = open(self.fuzz_file, "rb")
		self.fuzz_data = file.read()
		file.close()

	#this should be called from the mutation class...
	def fuzz_loop(self, mutation_data, timeout):
		
		#save mutation data to tmp file with same extension as self.fuzz_file
		ext = os.path.splitext(self.fuzz_file)[1]
		rand_name = "%d.FUZZFILE" % (random.randint(0,999999999))
		tmp_fn = self.fuzz_file.rstrip(ext) + "." + rand_name + ext
		file = open(tmp_fn, "wb")
		file.write(mutation_data)
		file.close()

		#upload file to device
		print "[%s] uploading file" % self.getName()
		if not adb.push_file(self.device, tmp_fn, "/mnt/sdcard/FUZZFILE" + ext):
			self.die("[%s] upload_file failed, dieing" % self.getName())

		#unlock the screen
		print "[%s] unlocking screen..." % self.getName()
		if not adb.unlock_screen(self.device):
			self.die("[%s] unlock_screen failed, dieing" % self.getName())

		#kill process if present
		#com.android.browser
		print "[%s] checking for process (music)" % self.getName()
		while adb.check_process(self.device, "android.music"):
			print "[%s] process found (music), killing" % self.getName()
			adb.kill_process(self.device, "android.music")
		#com.android.music
		#android.process.media??
		#print "[%s] checking for process (media)" % self.getName()		
		#if adb.check_process(self.device, "android.process.media"):
		#	print "[%s] process found (media), killing" % self.getName()	
		#	adb.kill_process(self.device, "android.process.media")

		#start process/intent with mutation_data_file arg
		print "[%s] starting activity\n" % self.getName()
		adb.start_activity_by_mime(self.device, "file:///mnt/sdcard/FUZZFILE" + ext, MIMETYPE)
		#adb.start_activity(self.device, "com.android.browser/com.android.browser.BrowserActivity", "file:///mnt/sdcard/FUZZFILE" + ext)
		#if not adb.start_activity(self.device, "com.android.browser/com.android.browser.BrowserActivity", "file:///mnt/sdcard/FUZZFILE" + ext):
			#self.die("[%s] start_activity failed, dieing" % self.getName())

		#sleep for timeout value
		print "[%s] sleeping for timeout" % self.getName()
		time.sleep(timeout)

		print "[%s] deleting test file from device" % self.getName()
		if not adb.delete_file(self.device, "/mnt/sdcard/FUZZFILE" + ext):
			print "[%s]    Oh Noes!! cant delete file..." % self.getName()
			adb.stop_adb()
			adb.start_adb()
			#self.restart()
			#self.die("[%s] delete_file failed, dieing" % self.getName())

		#pull crash log if present and save it with orig file and mutation file in individual directory
		print "[%s] checking for crashes" % self.getName()
		if adb.check_file(self.device, "/data/tombstones/tombstone*"):

			if not os.path.exists(CRASH_DIR + rand_name + "/"):
				os.makedirs(CRASH_DIR + rand_name + "/")

			adb.pull_file(self.device, "/data/tombstones/", CRASH_DIR + rand_name + "/")
				#if os.path.exists(CRASH_DIR + rand_name + "/" + "tombstone_00"):
			print "[%s]!!!!!!!!!!!!!!!!!!!!!!! CRASH !!!!!!!!!!!!!!!!!!!!!!!" % self.getName()
			shutil.copyfile(tmp_fn, CRASH_DIR + rand_name + "/crasher" + ext)
			shutil.copyfile(self.fuzz_file, CRASH_DIR + rand_name + "/orig" + ext)

			#	else:
			#		while (os.path.exists(CRASH_DIR + rand_name + "/")):
			#			shutil.rmtree(CRASH_DIR + rand_name + "/")
			#			time.sleep(1)

			adb.delete_file(self.device, "/data/tombstones/tombstone*")
			
	
		#delete tmp file
		print "[%s] deleting test file from host" % self.getName()
		if os.path.isfile(tmp_fn):
			os.remove(tmp_fn)

		if self.iteration_count > self.max_iterations:
			print "[%s] iteration_count > max_iterations, restarting" % self.getName()
			#self.restart()
			self.iteration_count = 0
		self.iteration_count += 1
		return
	
	
	def run(self):
		while (self.time_to_die == False):
			args = self.queue.get()
			self.fuzz_file = args[0]
			self.mutation_start = args[1]
			self.mutation_stop = args[2]
			self.mutation_method = args[3]
			self.update_fuzz_data()

			#block on remount
			print "[%s] waiting for adb to detect the emulator...." % self.getName()
			while True:
				#if we do this to many times and we dont have the correct # of emulators
				#we need to kill and restart adb
				devices = adb.check_devices()
				if type(devices) == type(None):
					time.sleep(2)
					continue
				for dev in devices:
					if dev.find(self.device.split("\t")[0]) > -1:
						self.device = dev
				if adb.remount(self.device, "/mnt/sdcard"):
					break
				else:
					#print "[%s] %s sleeping..." % (self.device, self.getName())
					time.sleep(2)

			#unlock the screen
			print "[%s] unlocking screen..." % self.getName()
			adb.unlock_screen(self.device)

			#mutate file (pass in data, max iteration, mutation method, this class)
			print "[%s]\n\tdevice: %s\n\tfuzz file: %s\n\tmethod: %s\n\titeration: %d %d" % (self.getName(), self.device.split("\t")[0], self.fuzz_file, self.mutation_method, self.mutation_start, self.mutation_stop)
			mut = Mutator(self.fuzz_loop, self.fuzz_data, self.fuzz_file.split("/")[-1], self.getName())
			mut.run(self.mutation_method, self.mutation_start, self.mutation_stop)
			print "[%s]\n\tdevice: %s\n\tcompleted mutations for file: %s\n\tmethod: %s" % (self.getName(), self.device.split("\t")[0], self.fuzz_file, self.mutation_method)
			self.queue.task_done()


#better death???
#	catch ctrl-c and do
#	popen.call(kill -9 %d % os.getpid() )
#


def wait_for_devices():
	adb.stop_adb()
	print "\n"
	adb.start_adb()
	print "\n"
	print "waiting for emulator instances to come online..."
	time.sleep(10)
	while True:
		devices = adb.check_devices()
		if devices == None:
			time.sleep(1)
		elif len(devices) < NUM_EMULATORS:
			time.sleep(1)
		else:
			break

	print "kicking off fuzzer threads..."
	dirlist = os.listdir(FUZZ_SAMPLE_DIR)
	queue = Queue.Queue()
	file_list = []
	for dirname, dirnames, filenames in os.walk(FUZZ_SAMPLE_DIR):
		if filenames:
			for filename in filenames:
				if filename.find("FUZZFILE") > -1:
					os.remove(os.path.join(dirname, filename))
				else:
					file_list.append(os.path.join(dirname, filename))

	print "using corpus:"
	for file in file_list:
		print "\t", file
		tmp = open(file, "rb")
		fuzz_data = tmp.read()
		tmp.close()
		mut = Mutator(None, fuzz_data)
		for primitive in PRIMITIVES:
			max_mut = mut.get_max_mutations(primitive)
			tmp = []
			part = max_mut / MAX_ITERATION
			if part < 1:
				part = 1
			for i in range(0, part):
				tmp.append((max_mut/part) * i)
			#for i in range(0, NUM_EMULATORS):
			#	tmp.append((max_mut/NUM_EMULATORS)*i)
			if tmp[-1] < max_mut:
				tmp.append(max_mut)
			for i in range(0, len(tmp)-1):
				queue.put([file, tmp[i], tmp[i+1], primitive])


	print "total instance iterations: ", len(list(queue.queue))


	for device in devices:
		thread = FuzzThread(device, queue)
		thread.setDaemon(True)
		thread.start()
	
	queue.join()

def main():
	avds = []

	#delete all emulator instances
	print "killing all emulator instances..."
	avd_dic =  emu.check_avd()
	for k, v in avd_dic.iteritems():
		#emu.kill_emulator(k)
		emu.delete_avd(k)

	#create new emulator instances
	print "creating new emulator instances..."
	for i in range(0, NUM_EMULATORS):
		emu.create_avd("fuzz_%d" % i, API_LEVEL)
		avds.append("fuzz_%d" % i)

	#create an sdcard for each emulator
	sdcards = []	
	if SDCARD:
		print "creating new sdcards for each emulator..."
		for i in range(0, NUM_EMULATORS):
			#emu.delete_sdcard("sdcard_%d" %i)
			emu.make_sdcard(512, "sdcard_%d" % i)
			sdcards.append("sdcard_%d" % i)

	#start um up
	print "starting up emulator instances..."
	for i in range(0, len(avds)):
		if SDCARD:
			emu.start_avd(avds[i], " -no-boot-anim -memory 2048 -partition-size 512 -sdcard %s" % sdcards[i])
		else:
			emu.start_avd(avds[i])

	#kicks off fuzz threads	
	wait_for_devices()

	#kills everything nicely
	avd_dic =  emu.check_avd()
	for k, v in avd_dic.iteritems():
		print "killing avd:", k
		emu.kill_emulator(k)
		#emu.delete_avd(k)
	

if __name__ == "__main__":
	main()
