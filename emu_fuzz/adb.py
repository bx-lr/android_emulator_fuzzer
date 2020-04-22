'''
adb class

this should contain code to interact with adb as well as return the output from adb commands

...

check for device:
	~/android-sdk-linux/platform-tools/adb devices

make /mnt/sdcard writeable:
	~/android-sdk-linux/platform-tools/adb shell mount -o remount,rw -t yaffs2 /dev/block/mtdblock3 /

upload fuzz file to sdcard:
	~/android-sdk-linux/platform-tools/adb push FUZZFILE.EXTENSION /sdcard/FUZZFILE.EXTENSION


make sure the screen is unlocked:
	~/android-sdk-linux/platform-tools/adb shell input keyevent 82
	~/android-sdk-linux/platform-tools/adb shell input keyevent 4

start activity to process the fuzz file:
	~/android-sdk-linux/platform-tools/adb shell am start -n com.android.browser/com.android.browser.BrowserActivity file:///sdcard/FUZZFILE.EXTENSION

if activity failed...
	goto delete fuzz file

sleep now....

check for crashlogs:
	~/android-sdk-linux/platform-tools/adb shell ls /data/tombstones/

if crash logs then pull um and fuzz file:
	~/android-sdk-linux/platform-tools/adb pull /data/tombstones/ crashes/
	~/android-sdk-linux/platform-tools/adb pull /sdcard/FUZZFILE  crashes/

kill browser if present:
	~/android-sdk-linux/platform-tools/adb shell ps | grep browser

delete fuzz file:
	~/android-sdk-linux/platform-tools/adb shell rm /sdcard/FUZZFILE*
	goto upload fuzz file
	


TODO fix unlock_screen, start_activity
'''
import subprocess
import Queue
import threading
import time

DEBUG = False


class ADB:
	def __init__(self, path="$ANDROID_SDK_PLATFORM_TOOLS"):
		self.path = path
		self.adb = path + "adb"


	def queue_stdout(self, out, queue):
		if DEBUG:
			print "[ADB] queue_stdout"
		tmp = out.readlines()
		if DEBUG:
			print "\t queue_stdout returned", tmp
		queue.put(tmp)
		out.close()


	def queue_stderr(self, err, queue):
		if DEBUG:
			print "[ADB] queue_stderr"
		tmp = err.readlines()
		if DEBUG:
			print "\t queue_stderr returned", tmp
		queue.put(tmp)
		err.close()


	def start_adb(self):
		if DEBUG:
			print "[ADB] start_adb"		
		try:
			cmd = self.adb
			cmd += " start-server"
			cmd = cmd.split(" ")
			p = subprocess.call(cmd)
		except:
			if DEBUG:
				print "\t start_adb returned False"
			return False
		if DEBUG:
			print "\t start_adb returned True"
		return True
	

	def stop_adb(self):
#import os
#mypass = 'some password'
#sudo_command = 'gedit'
#p = os.system('echo %s|sudo -S %s' % (mypass, sudo_command))

		if DEBUG:
			print "[ADB] stop_adb"
		try:
			cmd = self.adb
			cmd += " kill-server"
			cmd = cmd.split(" ")
			p = subprocess.call(cmd)
		except:
			if DEBUG:
				print "\t stop_adb returned False"
			return False
		if DEBUG:
			print "\t stop_adb returned True"
		return True


	def run_cmd(self, name, args):
		if DEBUG:
			print "[ADB] run_cmd"
		if name.split("\t")[1].find("offline") > -1:
			if DEBUG:
				print "\t run_cmd device offline"
			return None
		cmd = self.adb + " -s %s" % name.split("\t")[0]
		cmd += args
		if DEBUG:
			print "\t run_cmd", cmd
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#		return p

		queue = Queue.Queue()

		t1 = threading.Thread(target=self.queue_stdout, args=(p.stdout, queue))
		t1.daemon = True
		t1.start()
		
		t2 = threading.Thread(target=self.queue_stderr, args=(p.stderr, queue))
		t2.daemon = True
		t2.start()

		line = []

		try:
			line = queue.get(timeout=4)
		except:
			if DEBUG:
				print "\t run_cmd exception reading queue"
			pass

		if DEBUG:
			print "\t run_cmd returned: ", line
		p.kill()
		return line


	def check_devices(self):
		if DEBUG:
			print "[ADB] check_devices"
		cmd = self.adb
		cmd += " devices"
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		stdout = p.stdout.readlines()
		tmp = None
		for i in range(0, len(stdout)):
			if stdout[i].find("List of devices attached") > -1:
				tmp = stdout[i+1:]
		if  len(tmp[0]) < 2:
			if DEBUG:
				print "\t check_devices returned None"
			return None
		devices = []
		for t in tmp:
			if len(t) > 2:
				devices.append(t)
		if DEBUG:
			print "\t check_devices returned device"
		
		return devices
		

	def check_file(self, name, args):
		if DEBUG:
			print "[ADB] check_file"

		cmd = " shell ls -l %s" % args
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t check_file(1) returned false"
			return False
		
		if "".join(std_out_err).find("No such file or directory") > -1:
			if DEBUG:
				print "\t check_file(2) returned false"
			return False
		if len(std_out_err) < 1:
			if DEBUG:
				print "\t check_file(3) returned false"
			return False
		if DEBUG:
			print "\t check_file returned true"
		return True


	def pull_file(self, name, remote, local):
		if DEBUG:
			print "[ADB] pull_file"
		cmd = " pull %s %s" % (remote, local)
		std_out_err= self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t pull_file(1) returned false"
			return False
		stderr = "".join(std_out_err)
		if stderr.find("does not exist") > -1 or stderr.find("failed to copy") > -1 or stderr.find("No such file or directory") > -1:
			if DEBUG:
				print "\t pull_file(2) returned false"
			return False
		if DEBUG:
			print "\t pull_file returned true"
		return True

	def push_file(self, name, local, remote):
		if DEBUG:
			print "[ADB] push_file"
		cmd = " push %s %s" % (local, remote)
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t push_file(1) returned false"
			return False
		stderr = "".join(std_out_err)
		if stderr.find("No such file or directory") > -1 or stderr.find("Read-only file system") > -1:
			if DEBUG:
				print "\t push_file(2) returned false"
			return False
		if DEBUG:
			print "\t push_file returned true"
		return True


	def delete_file(self, name, remote):
		if DEBUG:
			print "[ADB] delete_file"
		cmd = " shell rm %s" % (remote)
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t delete_file(1) returned false"
			return False
		stderr = "".join(std_out_err)
		if len(stderr) > 0:
			if DEBUG:
				print "\t delete_file(2) returned false"
			return False
		if DEBUG:
			print "\t delete_file returned true"
		return True


	def remount(self, name, path):
		if DEBUG:
			print "[ADB] remount"
		cmd = " shell mount -o remount,rw -t yaffs2 /dev/block/mtdblock3 %s" % path
		std_out_err = self.run_cmd(name, cmd)

		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t remount(1) returned false"
			return False

		if "".join(std_out_err).find("Invalid") > -1:
			if DEBUG:
				print "\t remount(2) returned false"
			return False			

		cmd = " shell echo asdf > %s/test.txt" % path
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t remount(3) returned false"
			return False
		testfile = "%s/test.txt" % path
		std_out_err = self.check_file(name, testfile)
		
		if std_out_err:
			std_out_err = self.delete_file(name, testfile)
			if std_out_err:
				if DEBUG:
					print "\t remount returned true"
				return True
		if DEBUG:
			print "\t remount(4) returned false"
		return False
	

	def check_process(self, name, process):
		if DEBUG:
			print "[ADB] check_process"
		cmd = " shell ps"
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t check_process(1) returned false"
			return False
		for line in std_out_err:
			if line.find(process) > -1:
				if DEBUG:
					print "\t check_process returned true"
				return True
		if DEBUG:
			print "\t check_process(2) returned false"
		return False


	def kill_process(self, name, process):
		if DEBUG:
			print "[ADB] kill_process"
		cmd = " shell ps"
		std_out_err = self.run_cmd(name, cmd)
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t kill_process(1) returned false"
			return False
		pid = None
		for line in std_out_err:
			if line.find(process) > -1:
				tmp = line.split(" ")
				for t in tmp:
					try:
						pid = int(t)
					except:
						continue
					if pid:
						break
		if pid == None:
			if DEBUG:
				print "\t kill_process(2) returned false"
			return False
		cmd = " shell kill -9 %d" % pid
		std_out_err = self.run_cmd(name, cmd)
#		if not std_out_err:
#			if DEBUG:
#				print "\t kill_process(3) returned false"
#			return False
		stderr = "".join(std_out_err)
		if len(stderr) > 0:
			if DEBUG:
				print "\t kill_process(3) returned false"
			return False
		if DEBUG:
			print "\t kill_process returned true"
		return True


	def start_activity(self, name, activity, args=None):
		if DEBUG:
			print "[ADB] start_activity"
		cmd = " shell am start -n %s" % (activity)
		if args:
			cmd += " %s" % (args)
		std_out_err = self.run_cmd(name, cmd)
		if not std_out_err:
			if DEBUG:
				print "\t start_activity returned false"
			return False
		stderr = "".join(std_out_err)
		print stderr
		if DEBUG:
			print "\t start_activity returned true"
		return True

	def start_activity_by_mime(self, name, afile, mime):
	#am start -a android.intent.action.VIEW -d file:///sdcard/FUZZFILE.ogg -t audio/ogg
		if DEBUG:
			print "[ADB] start_activity_by_mime"
		cmd = " shell am start -a android.intent.action.VIEW -d %s -t %s" % (afile, mime)
		std_out_err = self.run_cmd(name, cmd)
		if not std_out_err:
			if DEBUG:
				print "\t start_activity_by_mime returned false"
			return False
		stderr = "".join(std_out_err)
		print stderr
		if DEBUG:
			print "\t start_activity_by_mime returned true"
		return True

	def unlock_screen(self, name):
		if DEBUG:
			print "[ADB] unlock_screen"
		cmd = " shell input keyevent"
		std_out_err = self.run_cmd(name, cmd + " 82")
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t unlock_screen(1) returned false"
			return False
		std_out_err = self.run_cmd(name, cmd + " 4")
		if type(std_out_err) == type(None):
			if DEBUG:
				print "\t unlock_screen(2) returned false"
			return False
		if DEBUG:
			print "\t unlock_screen returned true"
		return True
		
		

		
'''
testcases...
todo check all functions to see how they act if the emulator prematurely dies
'''

if __name__ == "__main__":			

	import time
	import sys
	import random
	import os

	adb = ADB("/home/udev/android-sdk-linux/platform-tools/")
	#print adb.stop_adb()
	#print adb.start_adb()
	dev = adb.check_devices()
	#if dev:
		#print adb.check_file(dev[0], "/")
		#print adb.delete_file(dev[0], "/mnt/sdcard/mutator.py")
		#unable_to_remount = True
		#while unable_to_remount:
		#	print dev[0]
		#	if adb.remount(dev[0], "/mnt/sdcard"):
		#		unable_to_remount = False
		#		print "remounted"
		#	time.sleep(5)
		#	print "Unable to remount..."
		#
		#print adb.unlock_screen(dev[0])
		#print adb.push_file(dev[0], "/home/udev/android-sdk-linux/platform-tools/htc_bug.ogg", "/mnt/sdcard/FUZZFILE.ogg")
		#print adb.pull_file(dev[0], "/mnt/sdcard/mutator.py", "test.txt")		
		#if adb.check_process(dev[0], "com.android.browser"):
		#	adb.kill_process(dev[0], "com.android.browser")
		#print adb.start_activity(dev[0], "com.android.browser/com.android.browser.BrowserActivity", "file:///sdcard/FUZZFILE.ogg")

		#CRASH_DIR = "/home/udev/android-sdk-linux/platform-tools/fuzz/crashes/"
		#while True:
		#	print adb.check_file(dev[0], "/data/tombstones/tombstone*")
		#	time.sleep(1)

		#rand_name = "%d.FUZZFILE/" % (random.randint(0,999999999))
		#if adb.check_file(dev[0], "/data/anr/"):
		#	if not os.path.exists(CRASH_DIR + rand_name):
		#		os.makedirs(CRASH_DIR + rand_name)
		#	adb.pull_file(dev[0], "/data/anr/", CRASH_DIR + rand_name)
		#	adb.delete_file(dev[0], "/data/anr/*")
			
			
			
		#p = adb.run_cmd(dev[0], " shell ls -l")
		#if p:
		#	stdout = p.stdout.readlines()
		#	for line in stdout:
		#		print line
		

































