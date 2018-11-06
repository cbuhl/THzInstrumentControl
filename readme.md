# THzInstrumentControl

## Problem, background:
Terahertz time domain spectroscopy is used to characterise the antennas I fabricate for my PhD project. A previous application for the data acquisition was written a long time ago, with very little maintainability. 

This implementation should hopefully provide that.

It's written with a quick and dirty approach, but it has been doing its job excellently.

## Prerequisites and intended use:
 - Python >= 3.5
 - Numpy >= 1.14
 - Matplotlib >= 2.2
 - PySerial >= 2.7
 - Pandas >= 0.23
 - PyQt5 >= 5.6.2
 
Execute wrapper.py.

It has been developed on a mac, but it is used on a win10 machine. The .ui file is drawn up with QtDesigner, and imported as such. It has been easy for me to maintain and adjust in that way.
In wrapper.py, there's two lines in the `__init__()` that sets whether it's in demo-mode.

Also note that the COM ports has to be set manually.


## Noteworthy nice bits
 - The live plotting. That works an absolute charm. The outline showed in the wrapper.py file should be shamelessly stolen and used by anyone writing scientific instrumentation GUIs in python. 
 
 
If you have suggestions for improvement, I'm all ears!
Scan accumulations has not been implemented yet.
 

__Licensed under GNU GPLv3.__
I'd be thrilled to hear from you if you benefit from this.
