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
		self.clientno=None
		self.last_action=None
		self.jclient=jack.Client("midish_ioselect")
		super().__init__('Preset', True)
      
	def fill_list(self):
		#zynthian_gui_config.zyngui.curlayer.load_io_list()
		self.list_data.append(('di',0,self.get_seq_info()))
		res=[]
		cmd="aseqdump -l"
		i=0
		#output=check_output("a2jmidi_bridge midish", shell=True)
		
		#lines=output.decode('utf8').split('\n')
		#for line in output:
			#logging.info("output =8> %s" %line)
		#output=check_output("a2jmidi_bridge midish/2", shell=True)
		#lines=output.decode('utf8').split('\n')
		#for line in output:
		#	logging.info("output =8> %s" %line)
		cmd="aseqdump -l"

		output=check_output(cmd, shell=True)
		lines=output.decode('utf8').split('\n')
		for f in lines:
			title=str.replace(f, '_', ' ')
			res.append((f,i,title))
			i=i+1

		#self.list_data=res
		hw_out=self.jclient.get_ports() + self.get_seq_info()
		#self.list_data.append(('di',0,self.get_seq_info()))
		
		for f,hw in enumerate(hw_out):
			title=str(hw.name)#.split(':')[0]
			res.append((self.set_select_path,i,title))
			i=i+1

		self.list_data=res
		#self.list_data.append(hw_out)
		self.list_data.append((self.set_select_path,0,"path"))
		self.list_data.append((self.set_start,0,"start"))

		#check_output('aseqdump -l/n', shell=True).decode('utf-8','ignore')
		super().fill_list()

	def show(self):
		self.index=zynthian_gui_config.zyngui.curlayer.get_preset_index()
		super().show()

	def select_action(self, i):
		if zynthian_gui_config.zyngui.curlayer.engine.nickname=='MS':
		#	zynthian_gui_config.zyngui.show_screen('info')
			zynthian_gui_config.zyngui.show_info('info what the %s' %self.list_data[i][0], 910)
			self.last_action=self.list_data[i][0]
			self.last_action()

		else:
			zynthian_gui_config.zyngui.curlayer.set_preset(i)
			zynthian_gui_config.zyngui.show_screen('seqcontrol')

	def set_select_path(self):
		self.select_path.set("Select io")

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
		hw_out=self.jclient.get_ports(is_output=True, is_physical=True, is_midi=True)
		if len(hw_out)==0:
			hw_out=[]
		#Add MIDI-IN (ttymidi) device ...
		ttymidi_out=self.jclient.get_ports("ttymidi", is_output=True, is_physical=False, is_midi=True)
		try:
			hw_out.append(ttymidi_out[0])
		except:
			pass

		logging.info("Physical Devices: " + str(hw_out))
		
		return list

	#def set_select_path(self):
	#	if zynthian_gui_config.zyngui.curlayer:
	#		self.select_path.set(zynthian_gui_config.zyngui.curlayer.get_bankpath())

#------------------------------------------------------------------------------
