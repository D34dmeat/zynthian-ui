#!/usr/bin/python3
# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian GUI
# 
# Zynthian GUI Sequencer-Control Class
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

import sys
import copy
import logging
import tkinter
from time import sleep
from string import Template
from datetime import datetime
from threading  import Lock

# Zynthian specific modules
from zyngine import zynthian_controller
from . import zynthian_gui_config
from . import zynthian_gui_controller
from . import zynthian_gui_selector

#------------------------------------------------------------------------------
# Configure logging
#------------------------------------------------------------------------------

# Set root logging level
logging.basicConfig(stream=sys.stderr, level=zynthian_gui_config.log_level)

#------------------------------------------------------------------------------
# Zynthian Instrument Controller GUI Class
#------------------------------------------------------------------------------

class zynthian_gui_seqcontrol(zynthian_gui_selector):
	mode=None

	ctrl_screens={}
	zcontrollers=[]
	screen_name=None
	

	zgui_controllers=[]
	zgui_controllers_map={}

	def __init__(self):
		super().__init__('Controllers',True)
		#self.lb_height=(zynthian_gui_config.display_height-zynthian_gui_config.topbar_height)-zynthian_gui_config.ctrl_height
		# Create Lock object to avoid concurrence problems
		self.lock=Lock();
		self.end=0
		self.selected_track=0
		self.playing=False
		# Create "pusher" canvas => used in mode "select"
		self.pusher= tkinter.Frame(self.main_frame,
			width=zynthian_gui_config.ctrl_width,
			height=zynthian_gui_config.ctrl_height-1,
			bd=0,
			highlightthickness=0,
			relief='flat',
			bg = zynthian_gui_config.color_bg)

		# Create song pos indicator
		self.ctrlbar= tkinter.Frame(self.main_frame,
			width=zynthian_gui_config.display_width-1,
			height=zynthian_gui_config.ctrl_height-1,
			bd=0,
			highlightthickness=0,
			relief='flat',
			bg = zynthian_gui_config.color_bg)

		# Create infopane
		self.infopane= tkinter.Frame(self.main_frame,
			width=zynthian_gui_config.ctrl_width,
			height=zynthian_gui_config.ctrl_height-1,
			bd=0,
			highlightthickness=0,
			relief='flat',
			bg = zynthian_gui_config.color_bg)
		self.tbar=None
		self.secselect=False
		self.song_pos=tkinter.StringVar()
		self.play_mode=tkinter.StringVar()
		self.play_mode.set("continue")
		self.bpm_mode=tkinter.StringVar()
		self.bpm_mode.set("continue")
		self.quant_mode=tkinter.StringVar()
		self.quant_mode.set("continue")
		self.metronome_mode=tkinter.StringVar()
		self.metronome_mode.set("continue")
	
	def transport_drag(self, event):
		canvas = event.widget
		canvasw=zynthian_gui_config.display_width-2#canvas.winfo_width()
		
		
		x1, y1 = ( event.x - 1 ), ( event.y - 1 )
		pos= round(self.end*(x1/canvasw))
		if self.secselect:
			self.update_selection(pos)
		else:
			self.update_transport(pos)
		
		#x = canvas.canvasx(event.x)
		#y = canvas.canvasy(event.y)
		#print canvas.find_closest(x, y)
	
	def transport_release(self, event):
		x1, y1 = ( event.x - 1 ), ( event.y - 1 )
		
		canvas = event.widget
		canvasw=canvas.winfo_width()
		#logging.debug("math canvas %s" % canvasw)
		#logging.debug("math canvas %s" % zynthian_gui_config.display_width)
		#logging.debug("math x1 %s" % x1)
		logging.debug("math end %s" % self.end)
		pos= round(self.end*(x1/canvasw))
		if self.secselect:
			self.update_selection(pos)
			zynthian_gui_config.zyngui.curlayer.engine.set_selection(pos)
		else:
			self.update_transport(pos)
			zynthian_gui_config.zyngui.curlayer.engine.set_pos(pos)
		
			
		
	def info_drag(self, event):
		label = event.widget
		labelw=label.winfo_width()
		x1, y1 = ( event.x - 1 ), ( event.y - 1 )
		if label == self.bpm_info:
			bpm=round(y1)
			if bpm<1:bpm=1
			zynthian_gui_config.zyngui.curlayer.engine.bpm_mode.set('bpm '+str(bpm))
		
		if label == self.qmode_info:
			bpm=round(y1/2)
			if bpm<2:bpm=2
			if bpm>32:bpm=32
			zynthian_gui_config.zyngui.curlayer.engine.quant_mode.set('1/'+str(bpm))
		#pos= round(self.end*(x1/canvasw))
		
	
	def info_release(self, event):
		x1, y1 = ( event.x - 1 ), ( event.y - 1 )
		label = event.widget
		#canvasw=label.winfo_width()
		if label == self.bpm_info:
			bpm=round(y1)
			zynthian_gui_config.zyngui.curlayer.engine.bpm_mode.set('bpm '+str(bpm))
		logging.debug("release infobar %s" % y1)
		if label == self.qmode_info:
			bpm=round(y1/2)
			if bpm<2:bpm=2
			if bpm>32:bpm=32
			zynthian_gui_config.zyngui.curlayer.engine.quant_mode.set('1/'+str(bpm))
			zynthian_gui_config.zyngui.curlayer.engine.quant_int=bpm
		#canvas.coords('tbar', 0, 25, x1, 75)
		#canvas.coords('tbar_pos', tp, 0)
		
		#pos= round(self.end*(x1/canvasw))
		
		#zynthian_gui_config.zyngui.curlayer.engine.bpm_mode.set(x1)
		#canvas.itemconfig('tbar_pos', text="Bar "+str(pos))
	



	def rec(self):
		if self.playing:
			#self.playing=False
			self.rec.flash(20)
			zynthian_gui_config.zyngui.curlayer.engine.rec()
		else:
			self.playing=True
			self.rec.flash()
			zynthian_gui_config.zyngui.curlayer.engine.rec()
		
	def pause(self):
		if self.playing:
			self.playing=False
			zynthian_gui_config.zyngui.curlayer.engine.pause()
		
			
	def stop(self):
		if self.playing:
			self.playing=False
		zynthian_gui_config.zyngui.curlayer.engine.stop_playback()
		
	def play(self):
		if self.playing:
			self.playing=False
			self.play.flash()
			zynthian_gui_config.zyngui.curlayer.engine.pause()
		else:
			self.playing=True
			self.play.flash()
			zynthian_gui_config.zyngui.curlayer.engine.play()
		
	
	def show_tracks(self):
		# from tkinter import messagebox
		# tracks_list=zynthian_gui_config.zyngui.curlayer.engine.get_tracks()
		# for track in tracks_list:
			# track=str.replace(track, '{', '')
			# track=str.replace(track, '}', '')
			# track=track.replace('\n', '')
			# track=track.split(' ')
		# msg = messagebox.showinfo( "tracks list", "%s" %tracks_list)
		zynthian_gui_config.zyngui.curlayer.engine.settings='settings'
		zynthian_gui_config.zyngui.show_modal('midishio')

	def show(self):
		#self.lb_frame.height=self.lb_height-zynthian_gui_config.ctrl_height
		self.build_ctrls()
		self.lb_frame.grid_forget()
		self.lb_frame.grid(row=1, column=0, rowspan=1, columnspan=3, padx=(0,2), sticky="w")
		super().show()
		
		
		self.build_ctrls()
		
		
		#self.click_listbox()

	def hide(self):
		if self.shown:
			super().hide()
			for zc in self.zgui_controllers: zc.hide()
			if self.zselector: self.zselector.hide()

	def fill_list(self):
		self.list_data=[]
		i=0
		self.list_data.append(('new track',i,'new track'))
		# for cscr in zynthian_gui_config.zyngui.curlayer.get_ctrl_screens():
		for cscr in zynthian_gui_config.zyngui.curlayer.engine.get_tracks(i):
				self.list_data.append((cscr,i,cscr))
				i=i+1
		self.index=zynthian_gui_config.zyngui.curlayer.get_active_screen_index()
		#logging.debug("get tracks %s" % (zynthian_gui_config.zyngui.curlayer.engine.get_tracks(i)))
		super().fill_list()

	def set_selector(self):
		if self.mode=='select': super().set_selector()

	#def get_controllers(self):
	#	return 

	def set_controller_screen(self):
		#Get Mutex Lock 
		self.lock.acquire()
		#Get controllers for the current screen
		if self.index==0:
			zynthian_gui_config.zyngui.curlayer.engine.new_track()
			self.fill_list()
		elif self.index==self.selected_track:
			zynthian_gui_config.zyngui.curlayer.engine.settings='track'
			zynthian_gui_config.zyngui.show_modal('midishio')
		else:
			self.selected_track=self.index
			iq=self.index-1
			zynthian_gui_config.zyngui.curlayer.engine.select_track(iq)
			logging.debug("selecting track %d => %s" % (iq,zynthian_gui_config.zyngui.curlayer.engine.track_list[iq]))
		#zynthian_gui_config.zyngui.curlayer.set_active_screen_index(self.index)
		#self.zcontrollers=zynthian_gui_config.zyngui.curlayer.get_active_screen()
		#Setup GUI Controllers
		if self.zcontrollers:
			logging.debug("SET CONTROLLER SCREEN %s" % (zynthian_gui_config.zyngui.curlayer.ctrl_screen_active))
			#Configure zgui_controllers
			i=0
			for ctrl in self.zcontrollers:
				try:
					#logging.debug("CONTROLLER ARRAY %d => %s" % (i,ctrl.name))
					self.set_zcontroller(i,ctrl)
					i=i+1
				except Exception as e:
					if zynthian_gui_config.raise_exceptions:
						raise e
					else:
						logging.error("Controller %s (%d) => %s" % (ctrl.short_name,i,e))
						self.zgui_controllers[i].hide()
			#Hide rest of GUI controllers
			for i in range(i,len(self.zgui_controllers)):
				self.zgui_controllers[i].hide()
		#Hide All GUI controllers
		else:
			for zgui_controller in self.zgui_controllers:
				zgui_controller.hide()
		#Release Mutex Lock
		self.lock.release()

	def set_zcontroller(self, i, ctrl):
		if i < len(self.zgui_controllers):
			self.zgui_controllers[i].config(ctrl)
			self.zgui_controllers[i].show()
		else:
			self.zgui_controllers.append(zynthian_gui_controller(i,self.main_frame,ctrl))
		self.zgui_controllers_map[ctrl]=self.zgui_controllers[i]

	def set_mode_select(self):
		self.mode='select'
		for i in range(0,4):
			self.zgui_controllers[i].hide()
		if zynthian_gui_config.select_ctrl>1:
			self.pusher.grid(row=2,column=0)
		else:
			self.pusher.grid(row=2,column=2)
		self.set_selector()
		self.listbox.config(selectbackground=zynthian_gui_config.color_ctrl_bg_on,
			selectforeground=zynthian_gui_config.color_ctrl_tx,
			fg=zynthian_gui_config.color_ctrl_tx)
		#self.listbox.config(selectbackground=zynthian_gui_config.color_ctrl_bg_off,
		#	selectforeground=zynthian_gui_config.color_ctrl_tx,
		#	fg=zynthian_gui_config.color_ctrl_tx_off)
		self.select(self.index)
		self.selected_track=self.index
		self.set_select_path()

	def set_mode_control(self):
		self.mode='control'
		if self.zselector: self.zselector.hide()
		self.pusher.grid_forget();
		self.set_controller_screen()
		self.listbox.config(selectbackground=zynthian_gui_config.color_ctrl_bg_on,
			selectforeground=zynthian_gui_config.color_ctrl_tx,
			fg=zynthian_gui_config.color_ctrl_tx)
		self.set_select_path()

	def select_action(self, i):
		self.set_mode_control()

	def next(self):
		self.index+=1
		if self.index>=len(self.list_data):
			self.index=0
		self.select(self.index)
		self.click_listbox()
		return True

	def switch_select(self):
		if self.mode=='control':
			self.set_mode_select()
		elif self.mode=='select':
			self.click_listbox()

	def zyncoder_read(self):
		#Get Mutex Lock
		self.lock.acquire()
		#Read Controller
		if self.mode=='control' and self.zcontrollers:
			for i, ctrl in enumerate(self.zcontrollers):
				#print('Read Control ' + str(self.zgui_controllers[i].title))
				self.zgui_controllers[i].read_zyncoder()
		elif self.mode=='select':
			super().zyncoder_read()
		#Release Mutex Lock
		self.lock.release()

	def get_zgui_controller(self, zctrl):
		for zgui_controller in self.zgui_controllers:
			if zgui_controller.zctrl==zctrl:
				return zgui_controller

	def get_zgui_controller_by_index(self, i):
		return self.zgui_controllers[i]

	def set_controller_value(self, zctrl, val=None):
		if val is not None:
			zctrl.set_value(val)
		for zgui_controller in self.zgui_controllers:
			if zgui_controller.zctrl==zctrl:
				zgui_controller.zctrl_sync()

	def set_controller_value_by_index(self, i, val=None):
		zgui_controller=self.zgui_controllers[i]
		if val is not None:
			zgui_controller.zctrl.set_value(val)
		zgui_controller.zctrl_sync()

	def get_controller_value(self, zctrl):
		for i in self.zgui_controllers:
			if self.zgui_controllers[i].zctrl==zctrl:
				return zctrl.get_value()

	def get_controller_value_by_index(self, i):
		return self.zgui_controllers[i].zctrl.get_value()

	def midi_learn(self, i):
		if self.mode=='control':
			zynthian_gui_config.zyngui.curlayer.midi_learn(self.zgui_controllers[i].zctrl)

	def midi_unlearn(self, i):
		if self.mode=='control':
			zynthian_gui_config.zyngui.curlayer.midi_unlearn(self.zgui_controllers[i].zctrl)

	def cb_listbox_release(self,event):
		if self.mode=='select':
			super().cb_listbox_release(event)
		else:
			dts=(datetime.now()-self.listbox_push_ts).total_seconds()
			#logging.debug("LISTBOX RELEASE => %s" % dts)
			if dts<0.3:
				zynthian_gui_config.zyngui.start_loading()
				self.click_listbox()
				zynthian_gui_config.zyngui.stop_loading()

	def cb_listbox_motion(self,event):
		if self.mode=='select':
			super().cb_listbox_motion(event)
		else:
			dts=(datetime.now()-self.listbox_push_ts).total_seconds()
			if dts>0.1:
				index=self.get_cursel()
				if index!=self.index:
					#logging.debug("LISTBOX MOTION => %d" % self.index)
					zynthian_gui_config.zyngui.start_loading()
					self.select_listbox(self.get_cursel())
					zynthian_gui_config.zyngui.stop_loading()
					sleep(0.04)

	def set_select_path(self):
		if zynthian_gui_config.zyngui.curlayer:
			self.select_path.set("midish sequencer" + zynthian_gui_config.zyngui.curlayer.get_presetpath())
			
	def loop(self):
		if zynthian_gui_config.zyngui.curlayer.engine.loop():
			self.play_mode.set("looping")
		else:
			self.play_mode.set("continue")
		#zynthian_gui_config.zyngui.show_modal('filtermod')
	
	def select_part(self):
		if self.secselect:
			self.secselect=False
			self.tbar.coords('sbar', 0, 10, 0, self.tbar.winfo_height()-2)
		else:
			self.secselect=True
			
	def quant_part(self):
		if self.secselect:
			self.secselect=False
		else:
			self.secselect=True
		
	def selection_actions(self):
		zynthian_gui_config.zyngui.curlayer.engine.settings='select_actions'
		zynthian_gui_config.zyngui.show_modal('midishio')

	def build_ctrls(self):

		#----------------------------------------------------------------
		# infopane
		#----------------------------------------------------------------
		button_width=5#int(zynthian_gui_config.display_width/9)
		self.infopane.grid(row=1, column=2, rowspan=2, columnspan=2, padx=(0,2), sticky="nw")

		#infopane labels
		#-------------------

		self.mode_info=tkinter.Label( self.infopane,
			font=zynthian_gui_config.font_listbox,
			textvariable = self.play_mode,
			relief = 'groove',
			width = 5,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,)

		self.bpm_info=tkinter.Label( self.infopane,
			font=zynthian_gui_config.font_listbox,
			text='bbpm',
			textvariable = zynthian_gui_config.zyngui.curlayer.engine.bpm_mode,
			relief = 'groove',
			width = 5,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,)
		

		self.curfilt_info=tkinter.Label( self.infopane,
			font=zynthian_gui_config.font_listbox,
			textvariable = zynthian_gui_config.zyngui.curlayer.engine.play_rec,
			relief = 'groove',
			width = 5,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,)

		self.qmode_info=tkinter.Label( self.infopane,
			font=zynthian_gui_config.font_listbox,
			textvariable = zynthian_gui_config.zyngui.curlayer.engine.quant_mode,
			relief = 'groove',
			width = 5,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,)

		self.mode_info.grid(row=0, column=0, padx=(0,2), sticky="nw")
		self.bpm_info.grid(row=1, column=0, padx=(0,2), sticky="nw")
		self.curfilt_info.grid(row=2, column=0, padx=(0,2), sticky="nw")
		self.qmode_info.grid(row=3, column=0, padx=(0,2), sticky="nw")
		
		self.bpm_info.bind( "<B1-Motion>", self.info_drag )
		self.bpm_info.bind( "<ButtonRelease-1>", self.info_release )
		self.qmode_info.bind( "<B1-Motion>", self.info_drag )
		self.qmode_info.bind( "<ButtonRelease-1>", self.info_release )


		#----------------------------------------------------------------
		# control bar
		#----------------------------------------------------------------

		self.ctrlbar.grid(row=2, column=0, rowspan=2, columnspan=3, padx=(0,2), sticky="sw")
		
		#song position indicator
		self.pos_indicator=tkinter.Label( self.main_frame,
			font=zynthian_gui_config.font_listbox,
			textvariable = zynthian_gui_config.zyngui.curlayer.engine.pos_label,
			relief = 'flat',
			width = 5,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,)
		#self.pos_indicator.grid(row=0, column=0, padx=(0,2), sticky="w")
		#self.pos_indicator.place(x = zynthian_gui_config.ctrl_width+5,y = zynthian_gui_config.ctrl_height+(zynthian_gui_config.ctrl_height/2))
		
		# buttons
		
		stop = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			text = "stop",
			relief = 'groove',
			command = zynthian_gui_config.zyngui.curlayer.engine.stop_playback)
		
		self.play = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove',text = "play", command = zynthian_gui_config.zyngui.curlayer.engine.play)	
			
		self.rec = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove',text = "rec", command = zynthian_gui_config.zyngui.curlayer.engine.rec)
			
		pause = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "pause", command = zynthian_gui_config.zyngui.curlayer.engine.pause)
		
		settings = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "Settings", command = self.show_tracks)
		
		loop = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', textvariable = self.play_mode, command = self.loop)
			
		metr = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', 
			textvariable = zynthian_gui_config.zyngui.curlayer.engine.metr, 
			command = zynthian_gui_config.zyngui.curlayer.engine.metr_mode)
		
		buttselect = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "select", command = self.select_part)
		
		quant = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "Quant", command = self.quant_part)
			
		save = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "Save", command = zynthian_gui_config.zyngui.curlayer.engine.save)

		sel_act = tkinter.Button(self.ctrlbar,
			bg=zynthian_gui_config.color_panel_bg,
			fg=zynthian_gui_config.color_panel_tx,
			width = button_width,
			activebackground=zynthian_gui_config.color_ctrl_bg_on,
			font=zynthian_gui_config.font_listbox,
			relief = 'groove', text = "Sel actions", command = self.selection_actions)
					
		# the transport bar	canvas
		transport = tkinter.Canvas(self.ctrlbar, width=zynthian_gui_config.display_width-2, height=79,
			bg=zynthian_gui_config.color_panel_bg,
			#fg=zynthian_gui_config.color_panel_tx,
			relief = 'groove')
		transport.grid(row=2, column=0, columnspan=9, padx=(0,2), sticky="we")	
		
		# transport bar
		tbar = transport.create_rectangle(2, 2, 2, 75, fill="blue", tags=('tbar'))
		transport.bind( "<B1-Motion>", self.transport_drag )
		transport.bind( "<ButtonRelease-1>", self.transport_release )

		# select transport bar
		sbar = transport.create_rectangle(2, 2, 2, 75, fill="green", tags=('sbar'))
		# transport.bind( "<B1-Motion>", self.transport_drag )
		# transport.bind( "<ButtonRelease-1>", self.transport_release )
		
		
		# transport pos text
		tbar_pos = transport.create_text(2, 2, fill="white",
			anchor="nw", 
			text = "Bar "+zynthian_gui_config.zyngui.curlayer.engine.song_pos[0], 
			tags=('tbar_pos'))
		self.tbar=transport
		
		stop.grid(row=1, column=1, padx=(0,2), sticky="w")
		self.play.grid(row=1, column=2, padx=(0,2), sticky="w")
		self.rec.grid(row=1, column=3, padx=(0,2), sticky="w")
		pause.grid(row=1, column=4, padx=(0,2), sticky="w")
		settings.grid(row=1, column=5, padx=(0,2), sticky="w")
		loop.grid(row=1, column=6, padx=(0,2), sticky="w")
		buttselect.grid(row=0, column=6, padx=(0,2), sticky="w")
		save.grid(row=0, column=5, padx=(0,2), sticky="w")
		sel_act.grid(row=0, column=4, padx=(0,2), sticky="w")
		metr.grid(row=0, column=3, padx=(0,2), sticky="w")
		self.pos_indicator.grid(row=1, column=2, padx=(0,2), sticky="w")

	def update_songlength(self,end):
		self.end=end
		
		
	def update_transport(self, args):
		canvasw=zynthian_gui_config.display_width-2
		if self.end<1:
			#self.end=zynthian_gui_config.zyngui.curlayer.engine.get_end()
			# if self.end<1:
			self.end=1
		if self.tbar != None:
			#logging.debug("update transport to => %s" % args)
			x1=args*(canvasw/self.end)
			self.tbar.coords('tbar', 0, 10, x1, self.tbar.winfo_height()-2)
			if x1<(canvasw-50):
				tp=x1
			else:
				tp=canvasw-50
			self.tbar.coords('tbar_pos', tp, 0)
			self.tbar.itemconfig('tbar_pos', text="Bar "+str(args))
			
	def update_selection(self, args):
		canvasw=zynthian_gui_config.display_width-2
		if self.end<1:
			self.end=1
		if self.tbar != None:
			#logging.debug("update transport to => %s" % args)
			x1=args*(canvasw/self.end)
			x=int(zynthian_gui_config.zyngui.curlayer.engine.song_pos[0])
			x=x*(canvasw/self.end)
			self.tbar.coords('sbar', x, 10, x1, self.tbar.winfo_height()-2)
			if x1<(canvasw-50):
				tp=x1
			else:
				tp=canvasw-50
			self.tbar.coords('tbar_pos', tp, 0)
			self.tbar.itemconfig('tbar_pos', text="Bar "+str(args))
		#d.place(x = zynthian_gui_config.ctrl_width+5,y = zynthian_gui_config.ctrl_height+150)
		#c.place(x = zynthian_gui_config.ctrl_width+50,y = zynthian_gui_config.ctrl_height+150)
		#B.place(x = zynthian_gui_config.ctrl_width+150,y = zynthian_gui_config.ctrl_height+150)
		#self.song_pos.set(zynthian_gui_config.zyngui.curlayer.engine.song_pos)
		
		
		#e.place(x = zynthian_gui_config.ctrl_width+190,y = zynthian_gui_config.ctrl_height+150)

#------------------------------------------------------------------------------
