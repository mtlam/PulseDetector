#!/usr/bin/env python
'''
Written by Michael Lam
'''

import random
import glob
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#from matplotlib.ticker import FormatStrFormatter, MultipleLocator
from matplotlib.figure import Figure
#from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.ticker import *#MultipleLocator, FormatStrFormatter, LogLocator

import sys
import time
import pyaudio
#import wave

if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk


DIR='cluster'
SEPARATOR_COLOR="#CCCCCC"
SLEEP_TIME=1

##==================================================
## Audio 
##==================================================

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

##==================================================
## Data Processing
##==================================================

def getvalue(value,default=0):
    try:
        value = float(value)
    except ValueError:
        value = default
    return value


def record(ax,canvas):
    p = pyaudio.PyAudio()

    RECORD_SECONDS = getvalue(var_duration.get(),default=5)

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")
    
    frames = []

    YMAX = 20000 #max for metronome near microphone

    ax.set_xlim(0,RECORD_SECONDS)
    ax.set_ylim(0,YMAX) 
    t=0
    
    STEP = 10

    ts0 = np.arange(CHANNELS*CHUNK*STEP)/float(CHANNELS*CHUNK) #10 = plotting timestep, 5 has a bit of lag.
    ts0 = np.arange(CHANNELS*CHUNK*STEP)/float(CHANNELS*CHUNK) * float(1024)/RATE #10 = plotting timestep, 5 has a bit of lag.
    ts = np.copy(ts0) - ts0[-1]#np.zeros(len(ts0))
    plt.ion()

    retvalt = []
    retvaly = []

    canvas.draw()#show()
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        if (i+1)%STEP==0:# or i==int(RATE/CHUNK*RECORD_SECONDS)-1:
            signal = b''.join(frames)
            signal = np.fromstring(signal,'Int16')
            #print min(ts+(i+1-10)*2048),max(ts+(i+1-10)*2048)
            ts = ts+ts0[-1]
            #print min(ts),max(ts)
            #signal = np.abs(signal)
            newmax = 1.1*np.max(signal)
            if newmax > YMAX:
                YMAX = newmax
                ax.set_ylim(0,YMAX)
            ax.plot(ts,signal,'k')
            canvas.draw()
            retvalt.extend(ts)
            retvaly.extend(signal)
            frames = []

            
    print("* done recording")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    plt.ioff()
    return np.array(retvalt),np.array(retvaly)


##==================================================
## GUI 
##==================================================

    

root = Tk.Tk()
#root.geometry('+1400+100')
root.geometry('650x550+100+100') #Not sure why grid is failing
root.wm_title("Pulse Detector")



## ----------
## Build primary GUI containers
## ----------

mainframe = Tk.Frame(root)
mainframe.grid(row=0)

figframe = Tk.Frame(mainframe)#, bd = 6, bg='red')
fig = Figure(figsize=(8.5,5), dpi=75)
fig.subplots_adjust(wspace=0.5,left=0.15) #left allows enough space for the yaxis label to be read.
canvas = FigureCanvasTkAgg(fig, figframe)
canvas.get_tk_widget().grid(row=0)#,side=Tk.TOP)#,fill='x')
canvas.show()

canvas._tkcanvas.grid(row=1)#, fill=Tk.BOTH, expand=1)

figframe.grid(row=0,column=0)

## ----------
## Tkinter Variables
## ----------
var_mode = Tk.IntVar()
var_fits_on = Tk.IntVar()
var_message = Tk.StringVar()



var_phase = Tk.StringVar()
var_period = Tk.StringVar()
var_amplitude = Tk.StringVar()
var_amplitudeconv = Tk.StringVar()

var_depth = Tk.StringVar()
var_width_top = Tk.StringVar()
var_width_bottom = Tk.StringVar()



var_pulseperiod = Tk.StringVar()
var_leftclicks = Tk.IntVar()
var_clickval = Tk.DoubleVar()

var_duration = Tk.StringVar()
var_clickmode = Tk.StringVar()
var_message = Tk.StringVar()

var_mode.set(-1)


## ----------
## Primary Window
## ----------


tdata = []
ydata = []

tmaxima = []
ymaxima = []
emaxima = []

gs = gridspec.GridSpec(2, 7)
ax_audiocurve = fig.add_subplot(gs[0,:-2])
ax_residcurve = fig.add_subplot(gs[1,:-2])
ax_template = fig.add_subplot(gs[0, -2:])






def redraw_axes():
    ax_audiocurve.set_ylabel('Intensity')
    ax_residcurve.set_xlabel('Time [seconds]')
    ax_residcurve.set_ylabel('Residuals [seconds]') 
    ax_template.set_yticklabels([])
    #ax_template.set_xticks([])
    ax_template.set_xlim(0.3,0.7)
    ax_template.set_xticks([0.3,0.7])

    ax_template.set_xlabel('Phase')
    ax_template.set_title('Template')
    canvas.draw()

def update_main(rec=True,clear=False):
    global tdata,ydata,tmaxima,ymaxima,emaxima
    ax_audiocurve_xlim = ax_audiocurve.get_xlim()
    ax_audiocurve_ylim = ax_audiocurve.get_ylim()
    ax_residcurve_xlim = ax_residcurve.get_xlim()
    ax_residcurve_ylim = ax_residcurve.get_ylim()

    ax_audiocurve.cla()
    ax_residcurve.cla()

    if clear:
        ax_audiocurve.plot(tdata,ydata,'k')       
        ax_audiocurve.set_ylim(ax_audiocurve_ylim) 
        ax_audiocurve.set_xlim(ax_audiocurve_xlim)
        ax_residcurve.set_xlim(ax_audiocurve_xlim)
        tmaxima = []
        ymaxima = []
        emaxima = []
        var_leftclicks.set(0)
    elif rec:
        tdata,ydata = record(ax_audiocurve,canvas)
        tmaxima = []
        ymaxima = []
        emaxima = []
        ax_residcurve.set_xlim(ax_audiocurve.get_xlim())

    redraw_axes()



def update_mainclear():#mode=-1):
    update_main(clear=False)



def onclick(event):
    global tdata,ydata,tmaxima,ymaxima,emaxima
#    print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
#        event.button, event.x, event.y, event.xdata, event.ydata)

    left = var_leftclicks.get()
    if left%2==1:# and left!=0:
        
        pastclick = var_clickval.get()

        inds = np.where(np.logical_and(pastclick<=tdata,tdata<=event.xdata))[0]
        ind = np.argmax(ydata[inds])
        #print tdata[inds][ind],ydata[inds][ind]
        tmaxima.append(tdata[inds][ind])
        ymaxima.append(ydata[inds][ind])
        ax_audiocurve_xlim = ax_audiocurve.get_xlim()
        ax_audiocurve_ylim = ax_audiocurve.get_ylim()
        
        ax_audiocurve.cla()
        #print len(tdata),len(ydata)
        ax_audiocurve.plot(tdata,ydata,'k')

        ax_audiocurve.set_xlim(ax_audiocurve_xlim)
        ax_audiocurve.set_ylim(ax_audiocurve_ylim)
        var_clickval.set(0)

        for i in range(len(tmaxima)):
            ax_audiocurve.plot(tmaxima,ymaxima,'bo')
        fit_model()

    else:
        ax_audiocurve.axvline(x=event.xdata,color='b')
        var_clickval.set(event.xdata)

    var_leftclicks.set(left+1)
    redraw_axes()

cid = fig.canvas.mpl_connect('button_press_event', onclick)




def fit_model():
    #global tmaxima
    global tdata,ydata,tmaxima

    if len(tmaxima)<2:
        return

    ax_residcurve.cla()
    ax_template.cla()

    pulseperiod = getvalue(var_pulseperiod.get())
    phase = getvalue(var_phase.get())
    period = getvalue(var_period.get())
    amplitude = getvalue(var_amplitude.get())
    
    var_amplitudeconv.set(str(amplitude*343)) #why 343? for the microphone?

    if pulseperiod == 0:
        tprimes = np.array(tmaxima)
    else:
        inds = np.where(tdata<pulseperiod)[0]
        leninds = len(inds)
        foldedtdata = tdata[inds]
        foldedydata = np.zeros(leninds)

        RECORD_SECONDS = getvalue(var_duration.get(),default=5)
        MAX = RECORD_SECONDS/pulseperiod - 1
        N = 0
        for n in np.arange(MAX,dtype=np.int):#+1?
            try:
                foldedydata += ydata[n*leninds:(n+1)*leninds]
                N+=1
            except ValueError:
                break
        foldedydata /= N#MAX
            
        #add in end data
        #end = ydata[MAX*leninds:]
        #foldedydata[:len(ends)] += end


#        for i,t in enumerate(tdata):
#            tval = t%pulseperiod
#            ind = np.argmin(np.abs(foldedtdata-tval))
#            foldedydata[ind] += ydata[i] 
            #ax_template.plot(tdata,ydata)
#        print foldedtdata[:100],foldedydata[:100]

        LENGTH = len(foldedydata)
        foldedydata = np.roll(foldedydata,LENGTH/2-np.argmax(foldedydata))

        phase = foldedtdata / foldedtdata[-1]

        ax_template.plot(phase,foldedydata,'k')

        #ax_template.set_xlim(0,foldedtdata[-1])
        ax_template.set_xlim(0.30,0.70)
        ax_template.set_ylim(0,1.05*np.max(foldedydata))
        #ylim = ax_audiocurve.get_ylim()
        #ax_template.set_ylim(ylim)
        




        #tprimes = np.array(tmaxima)
        #tprimes -= (tprimes/pulseperiod)
        tprimes = np.array(map(lambda t: t%pulseperiod,tmaxima))
    tprimes -= np.mean(tprimes)


    #test
    #if period != 0:
    #    XLIM = ax_audiocurve.get_xlim()[-1]
    #    t = np.linspace(0,XLIM,1000)
    #    omega = 2*np.pi/period
    #    ax_residcurve.plot(t,amplitude*np.sin(omega*t+phase)+pulseperiod*t,'r')
    if period != 0 and amplitude != 0:
        omega = 2*np.pi/period
        #tprimes -= amplitude*np.sin(omega*tprimes+phase)

        XLIM = ax_audiocurve.get_xlim()[-1]
        t = np.linspace(0,XLIM,1000)
        omega = 2*np.pi/period
        ax_residcurve.plot(t,amplitude*np.cos(omega*(t-phase)),'r') 
        ax_residcurve.plot(tmaxima,tprimes,'go')
        
        tprimes -= amplitude*np.cos(omega*(np.array(tmaxima)-phase))
        
    tprimes -= np.mean(tprimes)    

    var_message.set(str(np.sum(np.power(tprimes,2))/(len(tmaxima)-1))) #dof
    

    ax_residcurve.plot(tmaxima,tprimes,'bo')
    ax_residcurve.set_xlim(ax_audiocurve.get_xlim())

    ax_residcurve.axhline(y=0,color='0.50')
        
    redraw_axes()




def refresh():
    return


redraw_axes()

#only for testing!
#NavigationToolbar2TkAgg calls pack(), must put inside separate frame to work with grid()
toolbarframe = Tk.Frame(mainframe)
toolbarframe.grid(row=2,stick=Tk.W)
toolbar = NavigationToolbar2TkAgg(canvas, toolbarframe)
toolbar.update()
toolbar.grid(row=1,sticky=Tk.W)

separator = Tk.Frame(mainframe,width=600,height=2,bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=3,pady=2)

frame_buttons = Tk.Frame(mainframe)
frame_buttons.grid(row=4,sticky=Tk.W)




frame_record = Tk.Frame(frame_buttons)
frame_record.grid(row=0,column=0,padx=12,pady=2)



label_duration = Tk.Label(frame_record,text="Recording Duration [s]:")
label_duration.pack()#grid(row=0,column=0)#columnspan=2)#row=0,column=0,columnspan=2)
#blank = Tk.Label(frame_record,text=" ")
#blank.grid(row=0,column=1)
entry_duration = Tk.Entry(frame_record,width=7,textvariable=var_duration)
entry_duration.pack()#grid(row=1,column=0)

button_record = Tk.Button(frame_record,text="Record",command=update_main)
button_record.pack()#grid()#row=1,column=1)

#button_clear = Tk.Button(frame_record,text="Clear",command=clear_all)
#button_clear.pack()#grid()#row=1,column=1)


#blank = Tk.Label(frame_record,text=" ")
#blank.grid(row=2,column=1)


#button_redrawclear = Tk.Button(frame_period,text="Update",command=lambda: update_mainclear())
#button_redrawclear.grid(row=2,column=1)
#button_redraw = Tk.Button(frame_period,text="Redraw",command=lambda: update_main())
#button_redraw.grid(row=2,column=0)



separator = Tk.Frame(frame_buttons,width=2,height=100, bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=0,column=1,padx=2)




frame_parameters = Tk.Frame(frame_buttons)
frame_parameters.grid(row=0,column=2)


#checkbutton_model = Tk.Checkbutton(frame_parameters,text="Fit Model",variable=var_fits_on,command=fit_model)#lambda: update_main(mode=-1))
#checkbutton_model.grid(row=0,column=0)
#checkbutton_model.toggle()

label_period = Tk.Label(frame_parameters,text="Pulse Period [s]:")
label_period.grid(row=1,column=0)
entry_period = Tk.Entry(frame_parameters,width=7,textvariable=var_pulseperiod)
entry_period.grid(row=1,column=1)

button_updatemodel = Tk.Button(frame_parameters,text="Update Model",command=fit_model)
button_updatemodel.grid(row=2,column=1)
button_clearmaxima = Tk.Button(frame_parameters,text="Clear TOAs",command=lambda: update_main(clear=True))
button_clearmaxima.grid(row=3,column=1)




label_phase = Tk.Label(frame_parameters,text="Orbital Phase [s]:")
label_phase.grid(row=1,column=2)
entry_phase = Tk.Entry(frame_parameters,width=7,textvariable=var_phase)
entry_phase.grid(row=1,column=3)

label_period = Tk.Label(frame_parameters,text="Orbital Period [s]:")
label_period.grid(row=2,column=2)
entry_period = Tk.Entry(frame_parameters,width=7,textvariable=var_period)
entry_period.grid(row=2,column=3)


label_amplitude = Tk.Label(frame_parameters,text="Orbit Amplitude [s]:")
label_amplitude.grid(row=3,column=2)
entry_amplitude = Tk.Entry(frame_parameters,width=7,textvariable=var_amplitude)
entry_amplitude.grid(row=3,column=3)

label_amplitudeconv = Tk.Label(frame_parameters,text="Amplitude Conversion [m]:")
label_amplitudeconv.grid(row=4,column=2)
label_amplitudeconvnum = Tk.Label(frame_parameters,width=7,textvariable=var_amplitudeconv)
label_amplitudeconvnum.grid(row=4,column=3)


separator = Tk.Frame(mainframe,width=600,height=2,bg=SEPARATOR_COLOR,bd=1, relief=Tk.SUNKEN).grid(row=5,pady=2)


label_message = Tk.Label(mainframe,textvariable=var_message)
label_message.grid(row=6)



## ----------
## Buttons/Menus
## ----------

def busy(msg="Working...",sleep=0):
    var_message.set(msg)
    root.config(cursor="watch")
    root.update()#_idletasks() #need to work through queued items
    if sleep!=0:
        time.sleep(sleep)
        notbusy()

def notbusy():
    var_message.set("")
    root.config(cursor="")


def popup_about():
    title="About"
    text=["Cornell University Department of Astronomy",
          "NANOGrav",
          "Python code by Michael Lam 2014"]
    d = window_popup(root,title,text,WIDTH=50)
    root.wait_window(d.top)

#Why does this pop up twice?
def popup_commands():
    title="Commands"
    text=["Record: Record your audio data",
          "",
          "Fit Model: Shows the results of your fitting of the model",
          "",
          "All parameters are set to 0 by default."]
    d = window_popup(root,title,text,WIDTH=50)
    root.wait_window(d.top)


    d = window_popup(root,title,text,WIDTH=50)#,photo)
    root.wait_window(d.top)


class window_popup:
    def __init__(self,parent,title,txt,WIDTH=40):
        top = self.top = Tk.Toplevel(parent)
        top.title(title)
        top.geometry('+150+250')
        top.bind("<Return>",lambda event:self.ok())
        for i in range(len(txt)):
            if txt[i][:5]=="image":
                photo = eval(txt[i])
                label=Tk.Label(top,image=photo)
                label.image = photo # keep a reference!
                label.pack()
            else:
                Tk.Label(top,anchor=Tk.W,width=WIDTH,text=txt[i]).pack()
        b = Tk.Button(top,text="OK",command=self.ok)
        b.pack()
        b.focus_set()
    def ok(self):
        self.top.destroy()



def destroy(event):
    sys.exit()




## Bindings
#root.bind("<Return>",superdo)
root.bind("<Escape>", destroy)
root.bind("<Control-q>", destroy)
root.bind("<F1>",lambda event: popup_about())
root.bind("<F2>",lambda event: popup_commands())
#root.bind("<F3>",lambda event: popup_equations())
root.bind("<F10>",destroy)



menubar = Tk.Menu(root)

filemenu = Tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Exit",accelerator="Esc", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu = Tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About",accelerator="F1", command=popup_about)
helpmenu.add_command(label="Commands",accelerator="F2", command=popup_commands)
menubar.add_cascade(label="Help", menu=helpmenu)

# display the menu
root.config(menu=menubar)







#update_main()

#root.configure(cursor=("@/usr/X11R6/include/X11/bitmaps/star","/usr/X11R6/include/X11/bitmaps/starMask", "white", "black"))

root.mainloop()
#Tk.mainloop()
