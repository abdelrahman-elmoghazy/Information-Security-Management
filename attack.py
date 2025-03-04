import itertools
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

CORRECT_PASSWORD = "Abdo#"

def dictionary_attack(dictionary_file, output_box):
    """Attempts login using a predefined dictionary file."""
    try:
        with open(dictionary_file, "r") as file:
            for password in file:
                password = password.strip()
                output_box.insert(tk.END, f"Trying: {password}\n")
                output_box.yview(tk.END)  # Auto-scroll
                if password == CORRECT_PASSWORD:
                    output_box.insert(tk.END, f"[+] Correct password found: {password}\n")
                    return True
    except FileNotFoundError:
        output_box.insert(tk.END, "[!] Dictionary file not found!\n")
    
    output_box.insert(tk.END, "[-] Dictionary attack failed.\n")
    return False

def brute_force_attack(output_box):
    """Tries all possible 5-letter alphabetical combinations."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for guess in itertools.product(chars, repeat=5):
        guess_password = "".join(guess)
        output_box.insert(tk.END, f"Trying: {guess_password}\n")
        output_box.yview(tk.END)  
        if guess_password == CORRECT_PASSWORD:
            output_box.insert(tk.END, f"[+] Correct password found using brute force: {guess_password}\n")
            return True
    output_box.insert(tk.END, "[-] Brute force attack failed.\n")
    return False

def start_attack():
    username = username_entry.get()
    if not username:
        messagebox.showerror("Error", "Please enter a username!")
        return

    output_box.delete(1.0, tk.END)  
    output_box.insert(tk.END, f"[+] Starting attack for user: {username}\n")
    
    dictionary_file = "dictionary.txt"

    def attack_process():
        if not dictionary_attack(dictionary_file, output_box):
            output_box.insert(tk.END, "[+] Attempting brute force attack...\n")
            brute_force_attack(output_box)

    threading.Thread(target=attack_process, daemon=True).start()

root = tk.Tk()
root.title("Password Cracker")
root.geometry("500x400")
root.resizable(False, False)

tk.Label(root, text="Enter Username:").pack(pady=5)
username_entry = tk.Entry(root, width=40)
username_entry.pack(pady=5)

start_button = tk.Button(root, text="Start Attack", command=start_attack, bg="red", fg="white")
start_button.pack(pady=10)

output_box = scrolledtext.ScrolledText(root, width=60, height=15)
output_box.pack(pady=5)
root.mainloop()
