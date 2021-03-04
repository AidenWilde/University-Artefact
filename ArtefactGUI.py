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
        self.master.minsize(800, 640)
        self.master.maxsize(800, 640)
        self.widgets = []
        self.CreateCoreWidgets()
        self.master.update()

    def AddWidget(self, widgetType, text, func, column, row):
        widget = None
        widgetType = widgetType.lower()
        if(widgetType == "button"):
            widget = self.tkinterWrapper.NewButton(text, func, column, row)
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

    def CreateCoreWidgets(self):
        # Create widgets for main window functionality that 't be created externally
        self.quitButton = self.tkinterWrapper.NewButton("Quit", self.master.destroy, 3, 5)
