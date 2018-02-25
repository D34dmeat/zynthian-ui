# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Engine (zynthian_engine_midish)
# 
# zynthian_engine implementation for midish sequencer
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
import re
import copy
import logging
import alsaseq
from . import zynthian_engine
from . import zynthian_controller
#import zynthian_gui_config


#------------------------------------------------------------------------------
# Midish Engine Class
#------------------------------------------------------------------------------

class zynthian_engine_midish(zynthian_engine):

	# ---------------------------------------------------------------------------
	# Controllers & Screens
	# ---------------------------------------------------------------------------

	# Controller Screens
	_ctrl_screens=[
		['track1',['volume','expression','pan','sustain']]
	]

	# ---------------------------------------------------------------------------
	# Initialization
	# ---------------------------------------------------------------------------

	def __init__(self, zyngui=None):
		super().__init__(zyngui)
		self.name="Midish"
		self.nickname="MS"
		self.command=("/usr/local/bin/midish", "-v")

		self.media_dirs=[
			('_', os.getcwd()+"/data/midish/media"),
			('MY', os.getcwd()+"/my-data/midish/media")
		]
		self.song_pos=[]
		self.alsaid=None
		os.system("a2jmidi_bridge midish_out &")
		#for line in output:
		#	logging.info("output =8> %s" %line[0])
		os.system("j2amidi_bridge midish_in &")
		#output=self.get_cmdlist("j2amidi_bridge midish_in &")
		#for line in output:
		#	logging.info("output =8> %s" %line[0])


		self.start(True)
		self.reset()

	def reset(self):
		super().reset()
		self.soundfont_index={}
		#self.clear_midi_routes()
		#self.unload_unused_soundfonts()

	def stop(self):
		#print("what")
		self.proc_cmd("quit",2)
		super().stop()

	# ---------------------------------------------------------------------------
	# Layer Management
	# ---------------------------------------------------------------------------

	def add_layer(self, layer):
		super().add_layer(layer)
		layer.part_i=None
		self.setup_midish(layer)

	def del_layer(self, layer):
		super().del_layer(layer)
		#if layer.part_i is not None:
			#self.set_all_midi_routes()
		#self.unload_unused_soundfonts()

	# ---------------------------------------------------------------------------
	# MIDI Channel Management
	# ---------------------------------------------------------------------------

	def set_midi_chan(self, layer):
		self.setup_midish(layer)

	# ---------------------------------------------------------------------------
	# Bank Management
	# ---------------------------------------------------------------------------

	def get_bank_list(self, layer=None):
		return self.get_dirlist(self.media_dirs)

	#def set_bank(self, layer, bank):
		#pass
	#	if self.load_soundfont(bank[0]):
	#		self.unload_unused_soundfonts()

	# ---------------------------------------------------------------------------
	# Bank Management
	# ---------------------------------------------------------------------------

	def get_preset_list(self, bank):
		self.start_loading()
		preset_list=[]
		preset_list=self.get_filelist(bank[0], "sng")
		preset_list.append((bank[0],[0,0,0],"new song","sng"))
		self.stop_loading()
		return preset_list

	def set_preset(self, layer, preset, preload=False):
		logging.info("preset selected =8> nr: %s path: %s name: %s" %(preset[1], preset[0], preset[2]))
		if preset[2] !='new song':
		#logging.debug("Set Preset => Layer: %d, SoundFont: %d, Bank: %d, Program: %d" % (layer.part_i,sfi,midi_bank,midi_prg))
			self.proc_cmd('load "{0}"'.format(preset[0]))
		else:
			logging.warning("starting with a new song: %s" % preset[2])

	def cmp_presets(self, preset1, preset2):
		if preset1[3]==preset2[3] and preset1[1][0]==preset2[1][0] and preset1[1][1]==preset2[1][1] and preset1[1][2]==preset2[1][2]:
			return True
		else:
			return False

	# ---------------------------------------------------------------------------
	# Specific functions
	# ---------------------------------------------------------------------------

	def get_free_parts(self):
		free_parts=list(range(0,16))
		for layer in self.layers:
			try:
				free_parts.remove(layer.part_i)
			except:
				pass
		return free_parts

	def get_io_list(self):
		self.start_loading()
		io_list=[]
		output=self.get_cmdlist("aseqdump -l")
		#lines=output.decode('utf8').split('\n')
		for line in output:
			logging.info("output =8> %s" %line[0])

		

		#io_list.append((bank[0],[0,0,0],"new song","sng"))
		self.stop_loading()
		return io_list


	def load_soundfont(self, sf):
		if sf not in self.soundfont_index:
			logging.info("Loading SoundFont '%s' ..." % sf)
			# Send command to FluidSynth
			lines=self.proc_cmd("load \"%s\"" % sf, 20)
			# Parse ouput ...
			sfi=None
			cre=re.compile(r"loaded SoundFont has ID (\d+)")
			for line in lines:
				res=cre.match(line)
				if res:
					sfi=int(res.group(1))
			# If soundfont was loaded succesfully ...
			if sfi is not None:
				logging.info("Loaded SoundFont '%s' => %d" % (sf,sfi))
				# Re-select presets for all layers to prevent instrument change
				for layer in self.layers:
					if layer.preset_info:
						self.set_preset(layer, layer.preset_info)
				# Insert ID in soundfont_index dictionary
				self.soundfont_index[sf]=sfi
				# Return soundfont ID
				return sfi
			else:
				logging.warning("SoundFont '%s' can't be loaded" % sf)
				return False

	def setup_midish(self, layer):
		if layer.part_i is not None:
			# Clear and recreate all routes if the routes for this layer were set already
			self.set_all_midi_routes()
		else:
			# No need to clear routes if there is the only layer to add
			try:
				layer.part_i=self.get_free_parts()[0]
				logging.debug("ADD LAYER => PART %s" % layer.part_i)
			except:
				logging.error("ADD LAYER => NO FREE PARTS!")
			self.set_layer_midi_routes(layer)

	def unload_unused_soundfonts(self):
		#Make a copy of soundfont index and remove used soundfonts
		sf_unload=copy.copy(self.soundfont_index)
		for layer in self.layers:
			bi=layer.bank_info
			if bi is not None:
				if bi[2] and bi[0] in sf_unload:
					#print("Skip "+bi[0]+"("+str(sf_unload[bi[0]])+")")
					del sf_unload[bi[0]]
		#Then, remove the remaining ;-)
		for sf,sfi in sf_unload.items():
			logging.info("Unload SoundFont => %d" % sfi)
			self.proc_cmd("unload %d" % sfi,2)
			del self.soundfont_index[sf]

	def set_layer_midi_routes(self, layer):
		if layer.part_i is not None:
			midich=layer.get_midi_chan()
			#alsaseq.client('sequencer', 1, 1, False)
			#self.alsaid=alsaseq.id()
			result=self.get_io_list()
			#alsaseq.start()
			#lines=self.proc_get_lines()
			#for line in self.queue:
			#	logging.info("output =8> %s" %line)
			#logging.info("output =8> %s" %result)

			self.proc_cmd(
				'dnew 0 "midish_in" ro\n'.format(midich, layer.part_i, self.alsaid))
			self.proc_cmd('dnew 1 "midish_out" wo\n')
			self.proc_cmd("print [igetd]")
			self.proc_cmd("dinfo 0")
			self.proc_cmd("dinfo 1")
			self.proc_cmd("ls")
			self.proc_cmd("inew keyboard {0 1}")
			self.proc_cmd("onew output {1 1}")
			self.proc_cmd("print [iexists keyboard]")
			self.proc_cmd("print [oexists output]")

			self.proc_cmd("i")
			#self.proc_cmd('load "{0}"'.format("/zynthian/zynthian-ui/data/midish/media/songs/" + "sample.sng"))
			#self.proc_cmd("p")
			

	def set_all_midi_routes(self):
		self.clear_midi_routes()
		for layer in self.layers:
			self.set_layer_midi_routes(layer)

	def clear_midi_routes(self):
		self.proc_cmd("reset")

	def rec(self,*args):
		self.proc_cmd("r")
		logging.info("output =8> processing command rec")

	def get_tracks(self,*args):
		tracks=self.proc_cmd('print [tlist]')
		logging.info("output =8> processing command print tlist %s" %tracks)
		return tracks


	def pause(self,*args):
		self.proc_cmd("i")

	def play(self,*args):
		self.proc_cmd("p")

#******************************************************************************
