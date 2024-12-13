import tkinter
from tkinter import *
from tkinter import messagebox

global root
root = Tk()
root.title("File Transfer Application")
root.geometry(f"925x500+300+150")
root.configure(bg="#fff")
root.resizable(False, False)

# Background image
img = PhotoImage(file='image/login.png')
Label(root, image=img, bg='white').place(x=50, y=50)

frame = Frame(root, width=350, height=350, bg='white')
frame.place(x=480, y=70)

heading = Label(frame, text='Sign in', fg='#57a1f8', bg='white', font=('Microsoft Yahei UI Light', 23, 'bold'))
heading.place(x=100, y=5)

def un_enter(e):
    username.delete(0, 'end')

def un_leave(e):
    name = username.get()
    if name == '':
        username.insert(0, 'Username')

# Username box
username = Entry(frame, width=25, fg='black', border=0, bg='white', font=('Microsoft, YaHei UI Light', 11))
username.place(x=30, y=80)
username.insert(0, 'Username')
username.bind('<FocusIn>', un_enter)
username.bind('<FocusOut>', un_leave)

Frame(frame, width=295, height=2, bg='black').place(x=25, y=107)

#####------

def pw_enter(e):
    password.delete(0, 'end')

def pw_leave(e):
    name = password.get()
    if name == '':
        password.insert(0, 'Password')

# Password boxbox
password = Entry(frame, width=25, fg='black', border=00, bg='white', font=('Microsoft, YaHei UI Light', 11))
password.place(x=30, y=150)
password.insert(0, 'Password')
password.bind('<FocusIn>', pw_enter)
password.bind('<FocusOut>', pw_leave)

Frame(frame, width=295, height=2, bg='black').place(x=25, y=177)

Button(frame, width=39, pady=7, text='Sign in', bg='#57a1f8', fg='white', border=0).place(x=35, y=220)
label = Label(frame, text="Don't have an account?", fg='black', bg='white', font=('Microsoft Yahei UI Light', 9))
label.place(x=75, y=260)

register = Button(frame, width=6, text='Register', border=0, bg='white', cursor='hand2', fg='#57a1f8')
register.place(x=215, y=260)

root.mainloop()