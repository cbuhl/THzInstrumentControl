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
 
Execute wrapper.py.

In wrapper.py, there's two lines in the `__init__()` that sets whether it's in demo-mode.


## Noteworthy nice bits
 - The live plotting. That works an absolute charm. The outline showed in the wrapper.py file should be shamelessly stolen and used by anyone writing scientific instrumentation GUIs in python. 
 
 
If you have suggestions for improvement, I'm all ears!
 
 
Notes on licensing: Go ahead and use it. If you benefit from it, it's good. Buy me a beer if you meet me, and it seems reasonably. 
