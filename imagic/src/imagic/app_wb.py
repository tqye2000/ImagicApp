"""
Image Enhencing Tool
"""


import toga
from toga.widgets.webview import WebView

class WebWrapper(toga.App):
    def startup(self):
        # Create the main window
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Create a WebView widget and load the website
        web_view = WebView(url="https://removebj.streamlit.app")

        # Set the WebView as the main content
        self.main_window.content = web_view

        # Show the main window
        self.main_window.show()

def main():
    return WebWrapper("WebWrapper", "com.example.webwrapper")

if __name__ == "__main__":
    app = main()
    app.main_loop()
    