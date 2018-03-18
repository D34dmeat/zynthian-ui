#!/usr/bin/python3
# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian GUI
# 
# Zynthian GUI midish io Selector Class
# 
# Copyright (C) 2015-2016 Fernando Moyano <jofemodo@zynthian.org>
#
#******************************************************************************
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
# 
#******************************************************************************

import os
import sys
import signal
import logging
from time import sleep
from threading  import Thread
from subprocess import check_output, Popen, PIPE
import alsaseq
import jack


# Zynthian specific modules
from . import zynthian_gui_config
from . import zynthian_gui_selector

jclient=None
clientno=None


#------------------------------------------------------------------------------
# Configure logging
#------------------------------------------------------------------------------

# Set root logging level
logging.basicConfig(stream=sys.stderr, level=zynthian_gui_config.log_level)

#-------------------------------------------------------------------------------
# Zynthian Midish io Selection GUI Class
#-------------------------------------------------------------------------------

class zynthian_gui_midishio(zynthian_gui_selector):
	
	def __init__(self):	
		self.select_actions=[(self.clear_track,"tclr","Clear selection in current track"),
			(self.cut_track,"tcut","Cut selection in current track"),
			(self.insert_track,"tins","Insert blank selection in current track"),
			(self.copy_track,"tcopy","Copy selection in current track"),
			(self.paste_track,"tcut","Paste selection to current track"),
			(self.duplicate_selection_pre,"mdup 0","Duplicate selection of song before"),
			(self.duplicate_selection_post,"mdup","Duplicate selection of song after"),
			(self.quanta_selection,"tquanta","Quantizise selection of current track note on note off"),
			(self.quantf_selection,"tquantf","Quantizise selection of current track only note on")]

		self.clientno=None
		self.current_track=''
		self.last_action=None
		self.mode=''
		self.jclient=jack.Client("midish_ioselect")
		super().__init__('Preset', True)
      
	def set_mode(self):
		self.mode=zynthian_gui_config.zyngui.curlayer.engine.settings
		#return 'track_9'
	
	def get_mode(self):
		self.mode=zynthian_gui_config.zyngui.curlayer.engine.settings
		return self.mode
	
	def fill_list(self):
		#zynthian_gui_config.zyngui.curlayer.load_io_list()
		#self.list_data.append(('di',0,self.get_seq_info()))
		res=[]
		#cmd="aseqdump -l"
		i=0
		#output=check_output("a2jmidi_bridge midish", shell=True)
		
		#lines=output.decode('utf8').split('\n')
		#for line in output:
			#logging.info("output =8> %s" %line)
		#output=check_output("a2jmidi_bridge midish/2", shell=True)
		#lines=output.decode('utf8').split('\n')
		#for line in output:
		#	logging.info("output =8> %s" %line)
		# cmd="aseqdump -l"

		# output=check_output(cmd, shell=True)
		# lines=output.decode('utf8').split('\n')
		# for f in lines:
			# title=str.replace(f, '_', ' ')
			# res.append((f,i,title))
			# i=i+1

		#self.list_data=res self.jclient.get_ports()
		#hw_out=self.get_seq_info()
		#self.list_data.append(('di',0,self.get_seq_info()))
		
		# for f,hw in enumerate(hw_out):
			# title=str(hw.name)#.split(':')[0]
			# res.append((self.set_output,i,title))
			# i=i+1

		self.list_data=res
		
		logging.info("mode of operadus %s" %self.get_mode())
		self.current_track=zynthian_gui_config.zyngui.curlayer.engine.current_track
		#track info
		if self.mode =='track':
		
			logging.info("output =8> %s" %self.current_track)
			self.list_data.append((self.set_select_path,0,"Track Name: "+self.current_track))
			self.tinfo=zynthian_gui_config.zyngui.curlayer.engine.get_trackinfo(tname=self.current_track)
			self.list_data.append((self.set_select_path,0,"Track filter: "+self.tinfo['fname']))
			for line in self.tinfo['filtero']:
				if line!='{' or line!='}':
					self.list_data.append((self.set_select_path,0,line))
				
		if self.mode =='settings':
			for option in self.get_options():
				self.list_data.append((self.set_select_path,0,option))
				
				
		if self.mode =='select_actions':
			i=0
			for action in self.select_actions:
				self.list_data.append((action[0],i,action[2]))
		#self.list_data.append(hw_out)
		self.list_data.append((self.set_select_path,0,"empty"))
		#self.list_data.append((self.set_start,0,"start"))

		#check_output('aseqdump -l/n', shell=True).decode('utf-8','ignore')
		super().fill_list()

	def get_options(self):
		options=[]
		options.append("Current Bpm: %s"%zynthian_gui_config.zyngui.curlayer.engine.get_bpm())
		return options
	
	
	def show(self):
		self.index=zynthian_gui_config.zyngui.curlayer.get_preset_index()
		super().show()

	def select_action(self, i):
		# if zynthian_gui_config.zyngui.curlayer.engine.nickname=='MS':
		# #	zynthian_gui_config.zyngui.show_screen('info')
			# zynthian_gui_config.zyngui.show_info('info what the %s' %self.list_data[i][0], 1910)
			# self.last_action=self.list_data[i][0]
			# self.last_action()
		if self.mode =='select_actions':
			self.last_action=self.list_data[i][0]
			self.last_action(i)
		else:
			#zynthian_gui_config.zyngui.curlayer.set_preset(i)
			zynthian_gui_config.zyngui.show_screen('seqcontrol')

	def set_select_path(self):
		msg='midish'
		if self.mode =='track':
			msg='Track '+self.current_track
		
		self.select_path.set("Options for {}".format(msg))

	def set_output(self):
		self.jclient.activate()
		logging.info("connections to input %s chosen: %s"%(self.list_data[self.index][2] , str(self.jclient.get_all_connections(self.list_data[self.index][2]))))
		self.jclient.connect('midish_output:playback', self.list_data[self.index][2])
		#zynthian_gui_config.zyngui.curlayer.engine.set_output(arg)	
		self.jclient.deactivate()
		self.jclient.close()

	def filter_rules(self, rules):
		for rule in rules.split(' '):
			logging.info("rule %s" %rule)
	
	def cb_listbox_motion(self,event):
		if self.mode=='bselect':
			super().cb_listbox_motion(event)
		else:
			dts=(datetime.now()-self.listbox_push_ts).total_seconds()
			if dts>0.1:
				index=self.get_cursel()
				if index!=self.index:
					logging.debug("LISTBOX MOTION => %d" % self.index)
					zynthian_gui_config.zyngui.start_loading()
					#self.select_listbox(self.get_cursel())
					zynthian_gui_config.zyngui.stop_loading()
					sleep(0.04)	
	
	def set_start(self):
		zynthian_gui_config.zyngui.show_screen('seqcontrol')	

	def preselect_action(self):
		return zynthian_gui_config.zyngui.curlayer.preload_preset(self.index)

	def back_action(self):
		return zynthian_gui_config.zyngui.curlayer.restore_preset()
	
	def get_seq_info(self):
		list=[]
		#sequencer=alsaseq.Sequencer(clientname='billy',streams=alsaseq.SEQ_OPEN_OUTPUT)
		#connections=sequencer.connection_list()
		#for clientports in connections:
		#	clientname, clientid, portlist = clientports
		#	logging.info("port:  %3d    %s" %(clientid, clientname))
		#	list.append(clientid, clientid, clientname)

		#if self.clientno==None:
		#	alsaseq.client('sequencer',1,1,False)
		#	self.clientno=alsaseq.id()
		#logging.info("port:  %3d    %s" %(alsaseq.id(), alsaseq.status()))
		#hw_out=self.jclient.get_ports(is_output=True, is_physical=True, is_midi=True)
		hw_out=self.jclient.get_ports(is_midi=True)
		if len(hw_out)==0:
			hw_out=[]
		#Add MIDI-IN (ttymidi) device ...
		# ttymidi_out=self.jclient.get_ports("ttymidi", is_output=True, is_physical=False, is_midi=True)
		# try:
			# hw_out.append(ttymidi_out[0])
		# except:
			# pass

		logging.info("Physical Devices: " + str(hw_out))
		list=hw_out
		return list
	def clear_track(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def cut_track(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def insert_track(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def copy_track(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def paste_track(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def duplicate_selection_pre(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def duplicate_selection_post(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def quanta_selection(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	def quantf_selection(self, i):
		logging.info("select action: %s"%self.select_actions[i][1])
	#def set_select_path(self):
	#	if zynthian_gui_config.zyngui.curlayer:
	#		self.select_path.set(zynthian_gui_config.zyngui.curlayer.get_bankpath())

#------------------------------------------------------------------------------
