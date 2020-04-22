'''
log class

should be called from mutator

should open session file

should log thread id (if present), iteration count, mutation file, mutation method

should clear log

create sessions folder
	current/
	complete/

remove should move session to complete



'''

import os
import shutil

class Log():
	def __init__(self, method, fn):
		self.method = method
		self.fn = fn
			
	def log(self, txt):
		fd = open("%s-%s.session" % (self.method, self.fn), "a+")
		fd.write(txt)
		fd.close()
		return
	
	def remove(self):
		if os.path.exists("%s-%s.session" % (self.method, self.fn)):
			shutil.move("%s-%s.session" % (self.method, self.fn), "%s-%s.session.bak" % (self.method, self.fn))
		return		

	def get_last(self):
		if os.path.exists("%s-%s.session" % (self.method, self.fn)):
			fd = open("%s-%s.session" % (self.method, self.fn), "r")
			data = fd.readlines()
			fd.close()
			return data[-1]
		return ""
	
	
	
