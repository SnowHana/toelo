import tkinter as tk
from tkinter import messagebox
from footy.analysis_main import start_app


def run_footy_cli_command():
    # Here’s where you'd call or import your footy_cli logic
    # e.g., footy_cli.main(args)
    start_app()
    messagebox.showinfo("Info", "Footy CLI Command Executed!")


root = tk.Tk()
root.title("Footy CLI GUI")

run_button = tk.Button(root, text="Run Command", command=run_footy_cli_command)
run_button.pack(padx=20, pady=20)

root.mainloop()
