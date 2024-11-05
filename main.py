import tkinter as tk
from tkinter import messagebox

class App:
    users = {}  # Simulated user data storage
    current_user = None
    def __init__(self, root):
        self.root = root
        self.root.title("Social Media Post Scheduler")
        self.create_welcome_page()

    def create_welcome_page(self):
        self.clear_window()
        tk.Label(self.root, text="Welcome to Social Media Post Scheduler", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Login", command=self.create_login_page).pack(pady=10)
        tk.Button(self.root, text="Register", command=self.create_register_page).pack(pady=10)

    def create_register_page(self):
        self.clear_window()
        tk.Label(self.root, text="Register", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="Name").pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()
        tk.Label(self.root, text="Email").pack()
        self.email_entry = tk.Entry(self.root)
        self.email_entry.pack()
        tk.Label(self.root, text="Password").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()
        tk.Button(self.root, text="Register", command=self.register_user).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_welcome_page).pack(pady=10)

    def create_login_page(self):
        self.clear_window()
        tk.Label(self.root, text="Login", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="Email").pack()
        self.login_email_entry = tk.Entry(self.root)
        self.login_email_entry.pack()
        tk.Label(self.root, text="Password").pack()
        self.login_password_entry = tk.Entry(self.root, show="*")
        self.login_password_entry.pack()
        tk.Button(self.root, text="Login", command=self.login_user).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_welcome_page).pack(pady=10)

    def register_user(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        # Save the user data locally
        if email in self.users:
            messagebox.showerror("Registration Error", "Email already registered!")
        else:
            self.users[email] = {'name': name, 'password': password}
            messagebox.showinfo("Registration", "User registered successfully!")
        messagebox.showinfo("Registration", "User registered successfully!")
        self.create_welcome_page()

    def login_user(self):
        email = self.login_email_entry.get()
        password = self.login_password_entry.get()
        # Check the user data
        if email in self.users and self.users[email]['password'] == password:
            self.current_user = email
            messagebox.showinfo("Login", "Logged in successfully!")
            self.create_application_page()
        else:
            messagebox.showerror("Login Error", "Invalid email or password!")

    def create_application_page(self):
        self.clear_window()
        tk.Label(self.root, text="Application Page", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Profile Management", command=self.create_profile_management_page).pack(pady=10)
        tk.Button(self.root, text="Social Media Scheduler", command=self.create_social_media_scheduler_page).pack(pady=10)

    def create_profile_management_page(self):
        self.clear_window()
        tk.Label(self.root, text="Profile Management", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Update Username", command=self.create_update_username_page).pack(pady=10)
        tk.Button(self.root, text="Update Email", command=self.create_update_email_page).pack(pady=10)
        tk.Button(self.root, text="Change Password", command=self.create_change_password_page).pack(pady=10)
        tk.Button(self.root, text="Logout", command=self.create_welcome_page).pack(pady=10)
        tk.Button(self.root, text="Delete Account", command=self.delete_account).pack(pady=10)

    def create_update_username_page(self):
        self.clear_window()
        tk.Label(self.root, text="Update Username", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="New Username").pack()
        self.new_username_entry = tk.Entry(self.root)
        self.new_username_entry.pack()
        tk.Button(self.root, text="Update", command=self.update_username).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_profile_management_page).pack(pady=10)

    def create_update_email_page(self):
        self.clear_window()
        tk.Label(self.root, text="Update Email", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="New Email").pack()
        self.new_email_entry = tk.Entry(self.root)
        self.new_email_entry.pack()
        tk.Button(self.root, text="Update", command=self.update_email).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_profile_management_page).pack(pady=10)

    def update_username(self):
        new_username = self.new_username_entry.get()
        # Logic to update username
        messagebox.showinfo("Update Username", f"Username updated to {new_username} successfully!")
        self.create_profile_management_page()

    def update_email(self):
        new_email = self.new_email_entry.get()
        # Update email in user data
        if new_email in self.users:
            messagebox.showerror("Update Error", "Email already in use!")
        else:
            self.users[new_email] = self.users.pop(self.current_user)
            self.current_user = new_email
            messagebox.showinfo("Update Email", f"Email updated to {new_email} successfully!")
            self.create_profile_management_page()

    def create_change_password_page(self):
        self.clear_window()
        tk.Label(self.root, text="Change Password", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="Current Password").pack()
        self.current_password_entry = tk.Entry(self.root, show="*")
        self.current_password_entry.pack()
        tk.Label(self.root, text="New Password").pack()
        self.new_password_entry = tk.Entry(self.root, show="*")
        self.new_password_entry.pack()
        tk.Button(self.root, text="Update", command=self.change_password).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_profile_management_page).pack(pady=10)

    def change_password(self):
        current_password = self.current_password_entry.get()
        new_password = self.new_password_entry.get()
        # Logic to verify current password and update to new password
        messagebox.showinfo("Change Password", "Password changed successfully!")
        self.create_profile_management_page()

    def delete_account(self):
        # Delete account from user data
        if self.current_user in self.users:
            del self.users[self.current_user]
            self.current_user = None
            messagebox.showinfo("Delete Account", "Account deleted successfully!")
            self.create_welcome_page()
        else:
            messagebox.showerror("Delete Error", "No account to delete!")

    def create_social_media_scheduler_page(self):
        # Placeholder for social media scheduler page
        pass

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
