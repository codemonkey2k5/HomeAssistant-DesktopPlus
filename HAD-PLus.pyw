import webview
import threading
import time
import sys # For error handling

# Define the URL for your Home Assistant dashboard
# Replace with the correct URL for your Home Assistant instance
HA_DASHBOARD_URL = 'http://homeassistant.local:8123/dashboard-test/Primary'

# Define the refresh interval in seconds (1 hour = 3600 seconds)
REFRESH_INTERVAL = 3600

# Create the webview window
# This function is used to create and configure the graphical window.
# - 'Home Assistant': Sets the title of the window.
# - HA_DASHBOARD_URL: Specifies the URL to be loaded in the window.
# - x=-1, y=-1: Positions the window at the default center location.
# - width, height: Sets the dimensions of the window.
# - frameless=True: Removes the window border and title bar.
# - resizable=False: Prevents the user from resizing the window.
# - on_top=False: Determines if the window stays on top of other windows.
window = webview.create_window(
    'Home Assistant',
    HA_DASHBOARD_URL,
    x=-1, y=-1, width=2583, height=1449,
    frameless=True, resizable=False, on_top=False
)

# Function to refresh the window
# This function takes the window object and attempts to reload its content.
# It includes error handling to catch potential issues during the reload.
def refresh_window(window):
    """Refreshes the webview window with error handling."""
    try:
        # Reload the window content
        window.reload()
        print("Window refreshed successfully!")
    except Exception as e:
        # If an error occurs during reload, print an error message.
        print(f"Error refreshing window: {e}")
        # You might want to log this error to a file for later review.

# Function to schedule hourly refreshes
# This function runs in a separate thread to avoid blocking the main application.
# It schedules the window refresh at the specified interval.
def schedule_refresh(window):
    """Schedules the window to refresh every hour."""
    while True:
        try:
            # Wait for the specified refresh interval
            time.sleep(REFRESH_INTERVAL)
            # Call the refresh_window function to reload the window
            refresh_window(window)
        except Exception as e:
            # Handle any exceptions that occur within the thread
            print(f"Error in refresh thread: {e}")
            # You might want to add more sophisticated error handling or logging here.

# Create a separate thread for scheduling the refresh
# Running the refresh logic in a separate thread prevents the script from freezing.
# - target: Specifies the function to be executed in the thread.
# - args: Provides arguments to the target function (the window object).
refresh_thread = threading.Thread(target=schedule_refresh, args=(window,))

# Set the thread as a daemon thread
# Daemon threads are terminated automatically when the main program exits.
# This ensures a clean shutdown of the refresh thread when the window is closed.
refresh_thread.daemon = True

# Start the refresh thread
refresh_thread.start()

# Start the webview application with session persistence
# This is a blocking call and will keep the script running until the window is closed.
# - private_mode=False: Enables session persistence (cookies, etc.).
try:
    webview.start(private_mode=False)
except Exception as e:
    # Handle exceptions that may occur during the webview start
    print(f"Error starting webview: {e}")
    sys.exit(1) # Exit the script with an error code

# Optional: Join the thread to keep the main script running until the window is closed
# Although the webview.start() call is blocking, joining the thread ensures that the main script
# doesn't exit prematurely if the webview window were to close unexpectedly.
refresh_thread.join()
# HomeAssistant-DesktopPlus By IbGeek  6-22-2025 V1.0

