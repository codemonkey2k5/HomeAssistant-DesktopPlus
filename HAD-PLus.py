import webview

# Define the URL for your Home Assistant dashboard
url = 'http://homeassistant.local:8123/'

# Create the window and set both it's size and the coordinates of the top left of the window
# Line 12 is just the name of the script
# Line 14 is where you set the window size and it's location on your desktop
# Line 15 allows you to toggle window frames, if the window is resizable and if it is forced to be on top

window = webview.create_window(
    'Home Assistant',   
    url,
    x=-1, y=-1, width=2583, height=1449,
    frameless=True, resizable=False, on_top=False
)

# Start the webview with session persistence so you do not need to re-login every time
webview.start(private_mode=False)
