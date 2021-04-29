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

from math import nan, isnan
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog

df = None
events = []

# prompts the user to select a text file and inputs data as a pandas dataframe,
#  then finds potential experimental events and places their line numbers into
#  the event list
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
        label_file_name.config(text = filepath)
        button_get_event["state"] = "normal"
        button_file_dialog["state"] = "disabled"
    except FileNotFoundError:
        pass

# collects a remaining event and prompts the user if it is an experimental
#  event or just a comment
def get_event():
    global df
    global events
    curr_event = events.pop(0)
    text_display_clear()
    text_display_readonly(event_str(df.loc[curr_event]) + "\n")
    # ask the user to decide if we analyze this particular event
    message_box = tk.messagebox.askquestion("User Input Required", "Does this comment represent an experimental event?", icon = "question")
    if message_box == "yes":
        # run both types of analysis
        two_second_analysis(df, curr_event)
        thirty_second_analysis(df, curr_event)
    if not events:
        button_get_event["state"] = "disabled"

# displays the given string but disallows the user from typing in the text box
def text_display_readonly(string):
    text_display.configure(state = "normal")
    text_display.insert(tk.END, string)
    text_display.configure(state = "disabled")

# like text_display_readonly but clears the display instead
def text_display_clear():
    text_display.configure(state = "normal")
    text_display.delete(1.0, tk.END)
    text_display.configure(state = "disabled")

# returns a simple string representation of the given event (a row in df)
def event_str(event):
    return "Time from Start\t\t\t" + str(event["Time from Start"]) + "\nComment\t\t\t" + str(event["Comment"])

# performs a 2-second analysis on the provided dataframe at the event, given as a row number
def two_second_analysis(df, event_line_num):
    # select 30 seconds pre-event data and a range of post-event data (from 180 to 300 seconds, based on user input)
    while True:
        try:            
            answer_box = simpledialog.askstring(title = "User Input Required: 2-second analysis", prompt = "How many seconds of post-event data (180-300)?")
            post_event_data_range = int(answer_box)
        except ValueError:
            tk.messagebox.showwarning("Error", "Not a number")
            continue
        if post_event_data_range < 180 or post_event_data_range > 300:
            tk.messagebox.showwarning("Error", "Number is outside the valid range")
            continue
        else:
            break

    text_display_readonly("\n2-second analysis::\n")
    event_range = df.loc[event_line_num - 30 : event_line_num + post_event_data_range].copy()

    # removing outliers now
    q1 = event_range["BIO 1"].quantile(.25)
    q3 = event_range["BIO 1"].quantile(.75)
    iqr = q3 - q1

    # prompt user to enter a multiplier for iqr
    while True:
        try:            
            answer_box = simpledialog.askstring(title = "User Input Required: IQR multiplier", prompt = "What will the IQR multiplier be (1.5-3.0)?")
            multiplier = float(answer_box)
        except ValueError:
            tk.messagebox.showwarning("Error", "Not a number")
            continue
        if multiplier > 3 or multiplier < 1.5:
            tk.messagebox.showwarning("Error", "Number is outside the valid range")
            continue
        else:
            break

    # create a copy of the column
    event_range["BIO 1 Outliers Removed"] = event_range["BIO 1"]
    # replace any outliers with NaN
    event_range["BIO 1 Outliers Removed"].where(event_range["BIO 1"] < q3 + multiplier * iqr, nan, inplace=True)
    event_range["BIO 1 Outliers Removed"].where(event_range["BIO 1"] > q1 - multiplier * iqr, nan, inplace=True)

    # replacing tossed values
    event_range["BIO 1 Forecast Linear"] = event_range["BIO 1 Outliers Removed"]
    event_range["BIO 1 Forecast Linear"] = event_range["BIO 1 Forecast Linear"].interpolate()

    # subtract baseline average
    event_range["BIO 1 Baseline Avg Subtracted"] = event_range["BIO 1 Forecast Linear"]
    baseline_average = np.mean(event_range.loc[event_line_num - 5: event_line_num - 1]["BIO 1 Baseline Avg Subtracted"])
    event_range.loc[:, "BIO 1 Baseline Avg Subtracted"] -= baseline_average
    text_display_readonly("Baseline average = " + str(baseline_average) + "\n\n")
    text_display_readonly(event_range.to_string(max_rows = 10) + "\n\n")

    # average each two 1-second data points, so data is average of 2 seconds
    #text_display_readonly("Prune (average) each two 1-second data points:\n\n")
    del event_range["Date"]
    del event_range["Time from Start"]
    del event_range["Time Stamp"]
    #event_range.set_index(pd.to_timedelta(event_range["Time"]), inplace = True)
    del event_range["Time"]
    #event_range = event_range.resample("2S").mean().reset_index().assign(Time = lambda x: x.Time + pd.Timedelta("500 milliseconds")).iloc[:-1]
    #text_display_readonly(event_range.to_string(max_rows = 10) + "\n\n")

    '''fig, ax = plt.subplots()
    plt.scatter(event_range.index, event_range["BIO 1 Baseline Avg Subtracted"], alpha=0.5, s=10)
    ax.set_xlabel("timestamp from start (sec)", fontsize=11)
    ax.set_ylabel("BIO 1", fontsize=11)
    ax.set_title("BIO 1 change over time")
    ax.grid(True)
    fig.tight_layout()
    plt.savefig("timestamp_" + str(event_line_num) + "_2s_plot.png", dpi=900)'''

    # output in a cut-and-pasteable format for graphing
    event_range.to_csv("timestamp_" + str(event_line_num) + "_2s.csv", index = True)
    # with baseline average at the end
    file_obj = open("timestamp_" + str(event_line_num) + "_2s.csv", "a")
    file_obj.write("Baseline average = " + str(baseline_average))
    file_obj.close()

# performs a 30-second analysis on the provided dataframe at the event, given as a row number
def thirty_second_analysis(df, event_line_num):
    # select 300 seconds pre-event data and a range of post-event data (up to 3000 seconds, based on user input)
    while True:
        try:
            answer_box = simpledialog.askstring(title = "User Input Required: 30-second analysis", prompt = "How many seconds of post-event data (up to 3000)?")
            post_event_data_range = int(answer_box)
        except ValueError:
            tk.messagebox.showwarning("Error", "Not a number")
            continue
        if post_event_data_range < 0 or post_event_data_range > 3000:
            tk.messagebox.showwarning("Error", "Number is outside the valid range")
            continue
        else:
            break

    text_display_readonly("\n30-second analysis::\n")
    event_range = df.loc[event_line_num - 300 : event_line_num + post_event_data_range].copy()

    # removing outliers now
    q1 = event_range["BIO 1"].quantile(.25)
    q3 = event_range["BIO 1"].quantile(.75)
    iqr = q3 - q1

    # prompt user to enter a multiplier for iqr
    while True:
        try:            
            answer_box = simpledialog.askstring(title = "User Input Required: IQR multiplier", prompt = "What will the IQR multiplier be (1.5-3.0)?")
            multiplier = float(answer_box)
        except ValueError:
            tk.messagebox.showwarning("Error", "Not a number")
            continue
        if multiplier > 3 or multiplier < 1.5:
            tk.messagebox.showwarning("Error", "Number is outside the valid range")
            continue
        else:
            break

    # create a copy of the column
    event_range["BIO 1 Outliers Removed"] = event_range["BIO 1"]
    # replace any outliers with NaN
    event_range["BIO 1 Outliers Removed"].where(event_range["BIO 1"] < q3 + multiplier * iqr, nan, inplace=True)
    event_range["BIO 1 Outliers Removed"].where(event_range["BIO 1"] > q1 - multiplier * iqr, nan, inplace=True)

    # replacing tossed values
    event_range["BIO 1 Forecast Linear"] = event_range["BIO 1 Outliers Removed"]
    event_range["BIO 1 Forecast Linear"] = event_range["BIO 1 Forecast Linear"].interpolate()

    # subtract baseline average
    event_range["BIO 1 Baseline Avg Subtracted"] = event_range["BIO 1 Forecast Linear"]
    baseline_average = np.mean(event_range.loc[event_line_num - 15: event_line_num - 1]["BIO 1 Baseline Avg Subtracted"])
    event_range.loc[:, "BIO 1 Baseline Avg Subtracted"] -= baseline_average
    text_display_readonly("Baseline average = " + str(baseline_average) + "\n\n")
    text_display_readonly(event_range.to_string(max_rows = 10) + "\n\n")

    # average each thirty 1-second data points, so data is average of 30 seconds
    #text_display_readonly("Prune (average) thirty 1-second data points:\n\n")
    del event_range["Date"]
    del event_range["Time from Start"]
    del event_range["Time Stamp"]
    #event_range.set_index(pd.to_timedelta(event_range["Time"]), inplace = True)
    del event_range["Time"]
    #event_range = event_range.resample("30S").mean().reset_index().assign(Time = lambda x: x.Time + pd.Timedelta("15 seconds")).iloc[:-1]
    #text_display_readonly(event_range.to_string(max_rows = 10) + "\n\n")

    '''fig, ax = plt.subplots()
    plt.scatter(event_range.index, event_range["BIO 1 Baseline Avg Subtracted"], alpha=0.5, s=10)
    ax.set_xlabel("timestamp from start (sec)", fontsize=11)
    ax.set_ylabel("BIO 1", fontsize=11)
    ax.set_title("BIO 1 change over time")
    ax.grid(True)
    fig.tight_layout()
    plt.savefig("timestamp_" + str(event_line_num) + "_30s_plot.png", dpi=900)'''

    # output in a cut-and-pasteable format for graphing
    event_range.to_csv("timestamp_" + str(event_line_num) + "_30s.csv", index = True)
    # with baseline average at the end
    file_obj = open("timestamp_" + str(event_line_num) + "_30s.csv", "a")
    file_obj.write("Baseline average = " + str(baseline_average))
    file_obj.close()

window = tk.Tk()
window.resizable(0, 0)
window.title("biosensing-stats")
window.geometry("710x460")
button_file_dialog = tk.Button(window, height = 1, width = 10, text = "Select File", command = open_file_dialog)
button_file_dialog.place(x = 10, y = 10)
button_get_event = tk.Button(window, height = 1, width = 10, text = "Get Event", command = get_event)
button_get_event.place(x = 100, y = 10)
button_get_event["state"] = "disabled"
text_display = scrolledtext.ScrolledText(window, height = 25, width = 85)
text_display.place(x = 10, y = 45)
text_display.configure(state = "disabled")
label_file_name = tk.Label(window)
label_file_name.place(x = 190, y = 13)
window.mainloop()