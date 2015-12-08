#!/usr/bin/python
import test
import tkMessageBox
from Tkinter import *

top = Tk()
# Code to add widgets will go here...

def generate():
	test.parsedata(T.get())
	prog_list = test.main()
	output = sorted(list(prog_list), key=len)
	T2.insert(END, output[0])
	

def quit():
	top.quit()


T1 = Text(top, height=10, width=30)
T1.pack()
T1.insert(END, "Please input your exmple here!")

T2 = Text(top, height=10, width=30)
T2.pack()
T2.insert(END, "Here is the program!")

B1 = Button(top, text ="Generate", command = generate)
B1.pack()
B2 = Button(top, text ="quit", command = quit)
B2.pack()


top.mainloop()

