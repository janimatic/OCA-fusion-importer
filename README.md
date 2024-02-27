# OCA - Open Cel Animation importer for Resolve/Fusion

Imports Animation cells to Resolve/Fusion from [OCA](https://rxlaboratory.org/tools/oca), a *JSON* + *PNG*/*EXR* format.
Copy the the file OCAimport.py in "DaVinci Resolve\Support\Workflow Integration Plugins" folder
(ex: C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Workflow Integration Plugins).
It requieres Python (only tested with Python3)

For the moment this preference should be set manually :
Preferences>User>editing>Standard still duration = 1 frame

Requieres Davinci resolve Studio 17 or newer.

Python 3 must be correctly configured first (check by opening resolve console and trying to switch to python 3, 
if you get no error message, python3's working in resolve).
