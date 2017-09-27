import sys, time, utils, math

if utils.PQT5 == True:
	from PyQt5.QtCore import Qt, QTimer
	from PyQt5.QtWidgets import QApplication,QWidget, QLabel, QHBoxLayout,\
	QCheckBox, QVBoxLayout, QPushButton 
	from PyQt5.QtGui import QPalette, QColor
else:
	from PyQt4.QtCore import Qt, QTimer
	from PyQt4.QtGui import QPalette, QColor, QApplication, QWidget,\
	QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox
	
import pyqtgraph as pg
import numpy as np
import eyes17.eyemath17 as em


class Expt(QWidget):
	TIMER = 50
	RPWIDTH = 300
	RPGAP = 4
	AWGmin = 1
	AWGmax = 5000
	AWGval = 200

	xvals = [2., 3.0, 4.0, 5.0, 10]	# allowed X values
	NP = 500			# Number of samples
	TG = 1				# Number of channels
	MINDEL = 1			# minimum time between samples, in usecs
	MAXDEL = 1000
	delay = MINDEL		# Time interval between samples
	Xval = 1			# timebase list index
	
	TMIN = -5
	TMAX = 5
	VMIN = -5
	VMAX = 5
	MAXCHAN = 1
	Data    = [ [], [] ]
	traceWidget = [None]
	
	measured = False
	
	sources = ['A1','A2','A3', 'MIC']
	chanpens = ['y','g','w','m']     #pqtgraph pen colors

	NP = 500			# Number of samples
	TG = 10				# Number of channels
	
	def __init__(self, device=None):
		QWidget.__init__(self)
		self.p = device										# connection to the device hardware 

		try:
			self.p.select_range('A1',4)
			self.p.select_range('A2',4)
			self.p.set_sine(self.AWGval)
		except:
			pass

		self.pwin = pg.PlotWidget()							# pyqtgraph window
		self.pwin.showGrid(x=True, y=True)					# with grid
		ax = self.pwin.getAxis('bottom')
		ax.setLabel(self.tr('Voltage  A1'))	
		ax = self.pwin.getAxis('left')
		ax.setLabel(self.tr('Voltage (A2)'))
		self.pwin.disableAutoRange()
		self.pwin.setXRange(self.TMIN, self.TMAX)
		self.pwin.setYRange(self.VMIN, self.VMAX)
		self.pwin.hideButtons()								# Do not show the 'A' button of pg

		for ch in range(self.MAXCHAN):							# initialize the pg trace widgets
			self.traceWidget[ch] = self.pwin.plot([0,0],[0,0], pen = self.chanpens[ch])

		right = QVBoxLayout()							# right side vertical layout
		right.setAlignment(Qt.AlignTop)
		right.setSpacing(self.RPGAP)				

		H = QHBoxLayout()
		self.SaveButton = QPushButton(self.tr("Save Data to"))
		self.SaveButton.setMaximumWidth(90)
		self.SaveButton.clicked.connect(self.save_data)		
		H.addWidget(self.SaveButton)
		self.Filename = utils.lineEdit(150, self.tr('XYplot.txt'), 20, None )
		H.addWidget(self.Filename)
		right.addLayout(H)

		H = QHBoxLayout()
		l = QLabel(text=self.tr('WG'))
		l.setMaximumWidth(25)
		H.addWidget(l)
		self.AWGslider = utils.slider(self.AWGmin, self.AWGmax, self.AWGval,100,self.awg_slider)
		H.addWidget(self.AWGslider)
		self.AWGtext = utils.lineEdit(100, self.AWGval, 6, self.awg_text)
		H.addWidget(self.AWGtext)
		l = QLabel(text=self.tr('Hz'))
		l.setMaximumWidth(20)
		H.addWidget(l)
		right.addLayout(H)
		
		H = QHBoxLayout()
		l = QLabel(text=self.tr('Voltage range'))
		l.setMaximumWidth(100)
		H.addWidget(l)
		self.Xslider = utils.slider(0, len(self.xvals)-1, self.Xval, 100, self.set_range)
		H.addWidget(self.Xslider)
		l = QLabel(text=self.tr('Volts'))
		l.setMaximumWidth(60)
		H.addWidget(l)
		right.addLayout(H)

		self.Diffmode = QCheckBox(self.tr('show (A1-A2) Vs A2'))
		right.addWidget(self.Diffmode)
		self.Diffmode.stateChanged.connect(self.diff_mode)

		H = QHBoxLayout()
		self.Xmax = QLabel(text=self.tr(''))
		H.addWidget(self.Xmax)
		right.addLayout(H)
		
		H = QHBoxLayout()
		self.Ymax = QLabel(text=self.tr(''))
		H.addWidget(self.Ymax)
		right.addLayout(H)


		#------------------------end of right panel ----------------
		
		top = QHBoxLayout()
		top.addWidget(self.pwin)
		top.addLayout(right)
		
		full = QVBoxLayout()
		full.addLayout(top)
		self.msgwin = QLabel(text=self.tr('messages'))
		full.addWidget(self.msgwin)
				
		self.setLayout(full)
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(self.TIMER)
		

		#----------------------------- end of init ---------------
				
	def diff_mode(self):
		ax = self.pwin.getAxis('left')
		if self.Diffmode.isChecked() == False:
			ax.setLabel(self.tr('Voltage (A1-A2)'))
		else:		
			ax.setLabel(self.tr('Voltage (A2)'))
				
	def update(self):
		try:
			tvs = self.p.capture2(self.NP, self.TG)
			self.Data[0] = tvs[3]    # A2
			if self.Diffmode.isChecked() == False:
				self.Data[1] = tvs[1]   # A1
			else:
				self.Data[1] = tvs[1] - tvs[3]  # A1-A2
			for ch in range(self.MAXCHAN):
				self.traceWidget[ch].setData(self.Data[0], self.Data[1])		
		except:
			self.comerr()
			
		fa = em.fit_sine(tvs[0], self.Data[0])
		fb = em.fit_sine(tvs[0], self.Data[1])
		if fa != None and fb != None:
			self.Xmax.setText(self.tr('Xmax = %5.3f V'%fa[1][0]))
			self.Ymax.setText(self.tr('Ymax = %5.3f V'%fb[1][0]))
		else:
			self.Xmax.setText('')
			self.Ymax.setText('')
	
	def save_data(self):
		if self.measured == False: 
			return
		fn = self.Filename.text()
		dat = []
		for ch in range(2):
				dat.append( [self.timeData[ch], self.voltData[ch] ])
		self.p.save(dat,fn)
		self.msg('Traces saved to %s'%fn)
			
	def set_range(self, index):
		x = self.xvals[index]
		self.pwin.setXRange(-x, x)
		self.pwin.setYRange(-x, x)
		
	def set_wave(self):
		try:	
			res = self.p.set_sine(self.AWGval)
			self.msg('AWG set to %6.2f Hz'%res)
		except:
			self.comerr()
			return
		T = 1.0e6/res
		self.NP = 500
		self.TG = int(1+T/self.NP)
		#print T,self.NP, self.TG
		if self.TG < self.MINDEL:
			self.TG = self.MINDEL
		elif self.TG > self.MAXDEL:
			self.TG = self.MAXDEL


	def awg_text(self, text):
		val = float(text)
		if self.AWGmin <= val <= self.AWGmax:
			self.AWGval = val
			self.AWGslider.setValue(self.AWGval)
			self.set_wave()

	def awg_slider(self, val):
		if self.AWGmin <= val <= self.AWGmax:
			self.AWGval = val
			self.AWGtext.setText(str(val))
			self.set_wave()
		
	def msg(self, m):
		self.msgwin.setText(self.tr(m))

	def comerr(self):
		self.msgwin.setText('<font color="red">' + self.tr('Error. Try Device->Reconnect'))
				

if __name__ == '__main__':
	import eyes17.eyes
	dev = eyes17.eyes.open()
	app = QApplication(sys.argv)
	mw = Expt(dev)
	mw.show()
	sys.exit(app.exec_())
	
