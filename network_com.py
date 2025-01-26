#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import requests
import json
import time


class NetworkCom(object):
	def __init__(self, addr='http://192.168.1.6:80/'):
		self.addr = addr
		self.temp = 0.0
		self.temp2 = 0.0
		self.f_switch = False
		self.heater_power = 0
		self.old_heater_power = 0
		self.pump_parameters = {}
		self.has_changed = False
		self.values_to_send = {}
		self.thread = threading.Thread(target=self.process)
		self.last_tick = time.perf_counter()
		self.started = False
		self.running = False
	
	def start(self):
		print(self.running)
		if not self.running: 
			self.running = True
			self.thread.start()			
		print(self.running)
		self.started = True

	def stop(self):
		self.started = False

	def exit(self):
		self.running = False

	def process(self):
		
		while self.running:
			if not self.started: continue
			tick = time.perf_counter()
			if ((tick - self.last_tick) < 1):
				continue
			self.last_tick = tick

			if self.pump_parameters:
				self.values_to_send[u'pump'] = self.pump_parameters
			
			if (self.heater_power != self.old_heater_power):
				self.values_to_send['heater_power'] = self.heater_power
				self.old_heater_power = self.heater_power
			try:
				if len(self.values_to_send.keys()) > 0:		
					req = requests.post(self.addr, json=self.values_to_send, headers={'Accept': 'application/json'}, timeout=2)
					self.values_to_send = {}
				else:
					req = requests.get(self.addr, headers={'Accept': 'application/json'}, timeout=2)			
					
				if (req.status_code == 200):
					self.pump_parameters.clear()
					self.values_to_send.clear()
					res = req.json()
					if res.get('temp1'):
						self.temp = float(res.get('temp1'))
					if res.get('temp2'):
						self.temp2 = float(res.get('temp2'))
					if res.get('level') is not None:
						self.f_switch = bool(res.get('level'))
			except:
				pass

