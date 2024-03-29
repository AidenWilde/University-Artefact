import tkinter as tk
from TkinterWrapper import TkinterWrapper   

class ArtefactGUI(tk.Frame):
    def __init__(self, master=None):
        # Generic tkinter requirements
        super().__init__(master)
        self.master = master
        self.tkinterWrapper = TkinterWrapper(self.master)
        self.CreateMainWindow()

    def CreateMainWindow(self):
        self.master.title("Artefact")
        self.master.minsize(186,425)
        self.master.maxsize(186,425)
        self.widgets = []
        self.master.update()

    def AddWidget(self, widgetType, text, func, column, row, state=tk.NORMAL):
        widget = None
        widgetType = widgetType.lower()
        if(widgetType == "button"):
            widget = self.tkinterWrapper.NewButton(text, func, column, row, state)
        elif(widgetType == "label"):            
            widget = self.tkinterWrapper.NewLabel(text, column, row)

        self.widgets.append(widget)
        self.master.update()
        return widget

    def StartAutoRefresh(self):
        self.master.update()
        self.master.after(1000, self.StartAutoRefresh)

    def UpdateLabelWidget(self, label, text):
        self.tkinterWrapper.UpdateLabel(label, text)

    def DisableButton(self, button):
        if(button['state'] == tk.NORMAL):
            button['state'] = tk.DISABLED
        return button['state']

    def EnableButton(self, button):
        if(button['state'] == tk.DISABLED):
            button['state'] = tk.NORMAL
        return button['state']
        
