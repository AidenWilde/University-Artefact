import tkinter as tk

class TkinterWrapper:
    def __init__(self, tkMaster):
        self.master = tkMaster

    def NewButton(self, text, function, column, row, state=tk.NORMAL):
        """
        text : the text that the button will inherit
        function : the function the button will execute once clicked
        column : the column location in the grid
        row : the row location in the grid
        """
        button = tk.Button(self.master)
        button["text"] = text
        button["command"] = function
        button["state"] = state
        button.grid(column=column, row=row)
        button.config(width=20, height=5)
        return button

    def NewLabel(self, text, column, row):
        label = tk.Label(self.master, text=text, wraplength=150, justify="center")
        label.grid(column=column, row=row)
        label.config(width=20, height=5)
        return label

    def UpdateLabel(self, label, text):
        label.configure(text=text)