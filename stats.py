'''
Copyright 2020 Chase Hermreck

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import pandas as pd
import tkinter as tk
from tkinter import filedialog

df = None
events = []

# prompts the user to select a text file and inputs data as a pandas dataframe
def open_file_dialog():
    global df
    global events
    filepath = tk.filedialog.askopenfilename(initialdir = "./", title = "Select a File", filetypes = (("Text files", "*.txt*"), ("All files", "*.*")))
    try:
        df = pd.read_table(filepath, names = ["Date","Time","Time Stamp","Time from Start","BIO 1","Comment"], skiprows = 7)
        # strip whitespace from columns
        df["Date"] = df["Date"].str.strip()
        df["Time"] = df["Time"].str.strip()
        df["Comment"] = df["Comment"].str.strip()
        for i in range(0, df.shape[0]):
            # if we have a comment in any given row, we know an experimental event may have happened here
            if df.loc[i, "Comment"]:
                events.append(i)
        button_get_event["state"] = "normal"
    except FileNotFoundError:
        pass

def get_event():
    global df
    global events
    print(df.loc[events.pop(0)])

window = tk.Tk()
window.title("biosensing-stats")
window.geometry("700x450")
button_file_dialog = tk.Button(window, height = 1, width = 10, text = "Browse Files", command = open_file_dialog)
button_file_dialog.place(x = 10, y = 10)
button_get_event = tk.Button(window, height = 1, width = 10, text = "Get Event", command = get_event)
button_get_event.place(x = 100, y = 10)
button_get_event["state"] = "disabled"
window.mainloop()