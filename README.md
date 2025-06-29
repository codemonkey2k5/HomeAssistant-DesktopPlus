WHAT DOES HomeAssistant-DesktopPlus do?

HomeAssistant-DesktopPlus allows windows users to open HomeAssistant on their desktop.  But more!
You can have the window stay on top of other running programs.
You can have it with or without a window frame.   
You can lock the screen size or allow it to be resizable.
You can set the dash to reload at a given interval.
And you can set the exact coordinates of the window so that it always opens up in the same location.

USE CASE:
I created this script so that I could have HomeAssistant running borderless, size and coordinate locked so that it looks like a windows desktop background image, but it's fully functional.  
The default settings on a 4k screen will cover the entire background but not the windows taskbar.  

INSTALL INSTRUCTIONS:
Note this was tested on Windows 11 with Python 3.13.5

First you need to install Python if it is not already installed.  
If you need to install Python, head over to: https://www.python.org/downloads/  and click the button at the top to download the lates version.
Once Python is installed, open a windows terminal elevated and type the following:  pip install pywebview
Press Enter and let it install.  

Once this installed, copy the script to a folder of your choosing.  Next right click on it, and select "Show More Options" then select "Send to Desktop (Shortcut)".
This will give you a shortcut that will open your homeassistant.  You can then add that icon to your startup so that it will open on login.  


There is nothing stopping anyone from opening up more than one instance at a time.  
I run 2, one for each screen on my PC.  
As long as you use the auto-refresh option, you should be able to keep the screens open indefinitely.
