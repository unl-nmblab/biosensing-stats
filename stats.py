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

import tkinter as tk
from tkinter import filedialog

def open_file_dialog():
    filepath = tk.filedialog.askopenfilename(initialdir = "./", title = "Select a File", filetypes = (("Text files", "*.txt*"), ("All files", "*.*")))

window = tk.Tk()
window.title("biosensing-stats")
window.geometry("700x450")
button_file_dialog = tk.Button(window, height = 1, width = 10, text = "Browse Files", command = open_file_dialog)
button_file_dialog.place(x = 10, y = 10)
window.mainloop()