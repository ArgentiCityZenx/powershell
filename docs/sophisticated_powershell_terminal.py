import subprocess
import tkinter as tk
from tkinter import scrolledtext
from pygments import highlight
from pygments.lexers import PowerShellLexer
from pygments.formatters import HtmlFormatter
import threading
import queue

class PowerShellTerminal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PowerShell Terminal")
        self.geometry("800x600")
        
        self.command_history = []
        self.history_index = -1
        
        self.create_widgets()
        self.create_event_bindings()

        self.output_queue = queue.Queue()
        self.process = None
        self.running = False

    def create_widgets(self):
        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', font=("Courier", 12))
        self.output_text.pack(expand=True, fill='both')
        
        self.input_text = tk.Entry(self, font=("Courier", 12))
        self.input_text.pack(fill='x', padx=5, pady=5)

    def create_event_bindings(self):
        self.input_text.bind("<Return>", self.on_enter)
        self.input_text.bind("<Up>", self.on_up)
        self.input_text.bind("<Down>", self.on_down)

    def on_enter(self, event):
        command = self.input_text.get()
        if command:
            self.append_command_to_history(command)
            self.execute_command(command)
            self.input_text.delete(0, tk.END)

    def on_up(self, event):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self.input_text.delete(0, tk.END)
            self.input_text.insert(0, self.command_history[self.history_index])

    def on_down(self, event):
        if self.command_history:
            self.history_index = min(len(self.command_history) - 1, self.history_index + 1)
            self.input_text.delete(0, tk.END)
            self.input_text.insert(0, self.command_history[self.history_index])

    def append_command_to_history(self, command):
        self.command_history.append(command)
        self.history_index = len(self.command_history)

    def execute_command(self, command):
        if not self.running:
            self.running = True
            self.process = threading.Thread(target=self.run_powershell_command, args=(command,))
            self.process.start()
            self.after(100, self.process_output)

    def run_powershell_command(self, command):
        try:
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
            self.output_queue.put((result.stdout, result.stderr))
        except Exception as e:
            self.output_queue.put(("", str(e)))
        self.running = False

    def process_output(self):
        try:
            stdout, stderr = self.output_queue.get_nowait()
            self.output_text.configure(state='normal')
            if stdout:
                highlighted_stdout = highlight(stdout, PowerShellLexer(), HtmlFormatter())
                self.output_text.insert(tk.END, highlighted_stdout)
            if stderr:
                highlighted_stderr = highlight(stderr, PowerShellLexer(), HtmlFormatter())
                self.output_text.insert(tk.END, highlighted_stderr)
            self.output_text.configure(state='disabled')
            self.output_text.yview(tk.END)
        except queue.Empty:
            if self.running:
                self.after(100, self.process_output)

if __name__ == "__main__":
    app = PowerShellTerminal()
    app.mainloop()
