'''
emulator class

this should contain code to start/stop/create/delete/list an android emulator instance...

...
check for ADV device:
	/android-sdk-linux/tools/android list avd

if not present create AVD device:
	~/android-sdk-linux/tools/android create avd -n android_2.1 -t 3
	
if not present create sdcard for emulator:
	~/android-sdk-linux/tools/mksdcard 256M sdcard

start emulator with sdcard:
	~/android-sdk-linux/tools/emulator -partition-size 256 -sdcard sdcard -avd gnex_test


'''

import subprocess
import os
from threading import Thread
import time
import socket
import telnetlib

DEBUG = False

class Emulator:
	def __init__(self, path="$ANDROID_SDK_TOOLS"):
		self.path = path
		self.android = self.path + "android"
		self.mksdcard = self.path + "mksdcard"
		self.emulator = self.path + "emulator"
		self.emulator_thread = []
		self.emulator_name = []

	def set_path(self, path):
		self.path = path
		return

	def make_sdcard(self, size, name="sdcard"):
		if DEBUG:
			print "[EMU] make_sdcard"		
		if os.path.isfile(name):
			if DEBUG:
				print "\t make_sdcard returned false"	
			return False		
		cmd = self.mksdcard
		cmd += " %sM %s" % (size, name)
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		p.wait()
		if DEBUG:
			print "\t make_sdcard returned true"
		return True

	def delete_sdcard(self, name):
		if DEBUG:
			print "[EMU] delete_sdcard"
		if os.path.isfile(name):
			os.remove(name)
			if DEBUG:
				print "\t delete_sdcard returned true"
			return True
		if DEBUG:
			print "\t delete_sdcard returned false"
		return False

	def check_avd(self):
		if DEBUG:
			print "[EMU] check_avd"
		cmd = self.android
		cmd += " list avd"
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		p.wait()
		stdout = p.stdout.readlines()
		avd_dic = {}
		avd_name = None
		for line in stdout:
			if line.find("    Name: ") > -1:
				avd_name = line[10:-1]
				avd_dic[avd_name] = []
			if avd_name:
				avd_dic[avd_name].append(line)
		if DEBUG:
			print "\t check_avd returned"
		return avd_dic		

	def delete_avd(self, name):
		if DEBUG:
			print "[EMU] delete_avd"
		cmd = self.android
		cmd += " delete avd -n %s" % name
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		p.wait()
		stderr = p.stderr.readlines()
		if "".join(stderr).find("Error:") > -1:
			if DEBUG:
				print "\t delete_avd returned false"
			return False
		if DEBUG:
			print "\t delete_avd returned true"
		return True
				

	def create_avd(self, name, api_level):
		if DEBUG:
			print "[EMU] create_avd"
		cmd = self.android
		cmd += " create avd -n %s -t %s" % (name, api_level)
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		result =  p.communicate("n\n")
		if "".join(result).find("Error:") > -1:
			if DEBUG:
				print "\t create_avd returned false"
			return False
		if DEBUG:
			print "\t create_avd returned true"
		return True

	def check_avd_targets(self):
		if DEBUG:
			print "[EMU] check_avd_targets"
		cmd = self.android
		cmd += " list targets"
		cmd = cmd.split(" ")
		p = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		p.wait()
		stdout = p.stdout.readlines()
		tmp = []
		for line in stdout:
			if line.find("android-") > -1:
				line = line.split(" ")
				tmp.append(line[-1].replace('"', "").replace("\n", ""))
		if DEBUG:
			print "\t check_avd_targets returned"
		return tmp

	def start_avd(self, name, arg=""):
		if DEBUG:
			print "[EMU] start_avd"
		thread = Thread(target = self.start_avd_thread, args=(name, arg,))
		thread.start()
		time.sleep(1)
		if not thread.isAlive():
			if DEBUG:
				print "\t start_avd returned false"
			return False
		self.emulator_thread.append(thread)
		self.emulator_name.append(name)
		if DEBUG:
			print "\t start_avd returned true"
		return True

	def start_avd_thread(self, name, arg):
		if DEBUG:
			print "[EMU] start_avd_thread"
		cmd = self.emulator
		cmd += " -avd %s" % name 
		cmd += arg
		cmd = cmd.split(" ")
		p = subprocess.call(cmd)
		if DEBUG:
			print "\t start_avd_thread returned"
		return 
		
	def kill_emulator(self, name):
		if DEBUG:
			print "[EMU] kill_emulator"
		if name not in self.emulator_name:
			if DEBUG:
				print "\t kill_emulator returned false"
			return False
		cmd = "ps -a -u -x"
		cmd = cmd.split(" ")
	        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		stdout = p.stdout.readlines()
		pid = None
		for line in stdout:
			if line.find(name) > -1:
				tmp = line.split(" ")
				for t in tmp:
					try:
						pid = int(t)
					except:
						pass
					if pid:
						break
		cmd = "kill -9 %d" % pid
		cmd = cmd.split(" ")
		p = subprocess.call(cmd)
		idx = self.emulator_name.index(name)
		self.emulator_name.pop(idx)
		self.emulator_thread.pop(idx)
		if DEBUG:
			print "\t kill_emulator returned true"
		return True

	def get_running_avd_args(self, name):
		if DEBUG:
			print "[EMU] get_running_avd_args"
		cmd = "ps -a -u -x"
		cmd = cmd.split(" ")
	        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		stdout = p.stdout.readlines()
		for line in stdout:
			if line.find(name) > -1:
				return line.split(name)[1]

	def get_running_avd(self, name):
		#use the name to kill, delete, and start new emulator
		if DEBUG:
			print "[EMU] get_running_avd"
		port = int(name.split("-")[1])
		tn = telnetlib.Telnet("localhost", port)
		tn.read_until("OK")
		tn.write("avd name\n")
		avd_name = tn.read_until("OK").split("\n")[1].rstrip("\r")
		tn.close()
		return avd_name
		

'''
testcases...
'''
if __name__ == "__main__":
	emu = Emulator("/home/udev/android-sdk-linux/tools/")
	#print emu.delete_sdcard("sdcard")
	size = 512
	sdcard = "sdcard_"
	#print emu.make_sdcard("512", "sdcard")
	#print emu.check_avd_targets()
	avd_dic =  emu.check_avd()
	i = 0
	if avd_dic:
		for key, value in avd_dic.iteritems():
			print "starting avd:", key
			print emu.start_avd(key, "  -partition-size %d -sdcard %s%d" % (size, sdcard, i))
			i += 1
			break

	#print emu.delete_avd("android_2.3.3")
	#print emu.create_avd("android_2.3.3", "android-10")
	#time.sleep(3)
#	for key, value in avd_dic.iteritems():
#		print "killing avd:", key
#		print emu.kill_emulator(key)
#		break



