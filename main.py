import tkinter as tk
from tkinter import messagebox

# User class to store individual user data
class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

# UserManager class to handle user data storage and operations
class UserManager:
    def __init__(self):
        self.users = {}  # key: email, value: User object
        self.current_user = None

    def register_user(self, name, email, password):
        if email in self.users:
            return False  # Registration failed
        else:
            self.users[email] = User(name, email, password)
            return True  # Registration successful

    def login_user(self, email, password):
        if email in self.users and self.users[email].password == password:
            self.current_user = self.users[email]
            return True
        else:
            return False

    def logout_user(self):
        self.current_user = None

    def delete_account(self):
        if self.current_user:
            del self.users[self.current_user.email]
            self.current_user = None
            return True
        else:
            return False

    def update_username(self, new_username):
        if self.current_user:
            self.current_user.name = new_username
            return True
        else:
            return False

    def update_email(self, new_email):
        if new_email in self.users:
            return False  # Email already in use
        else:
            if self.current_user:
                self.users[new_email] = self.users.pop(self.current_user.email)
                self.current_user.email = new_email
                return True
            else:
                return False

    def change_password(self, current_password, new_password):
        if self.current_user and self.current_user.password == current_password:
            self.current_user.password = new_password
            return True
        else:
            return False

# Main application class to manage frames and user manager
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Social Media Post Scheduler")
        self.user_manager = UserManager()
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        # Configure the grid
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Initialize frames dict
        self.frames = {}
        for F in (WelcomePage, RegisterPage, LoginPage, ApplicationPage, ProfileManagementPage, UpdateUsernamePage, UpdateEmailPage, ChangePasswordPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            # Put all pages in the same location;
            # The one on the top of the stacking order
            # will be the one that is visible
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("WelcomePage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

# Welcome page class
class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Welcome to Social Media Post Scheduler", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Login", command=lambda: controller.show_frame("LoginPage")).pack(pady=10)
        tk.Button(self, text="Register", command=lambda: controller.show_frame("RegisterPage")).pack(pady=10)

# Register page class
class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Register", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="Name").pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()
        tk.Label(self, text="Email").pack()
        self.email_entry = tk.Entry(self)
        self.email_entry.pack()
        tk.Label(self, text="Password").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        tk.Button(self, text="Register", command=self.register_user).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("WelcomePage")).pack(pady=10)

    def register_user(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        success = self.controller.user_manager.register_user(name, email, password)
        if success:
            messagebox.showinfo("Registration", "User registered successfully!")
            self.controller.show_frame("WelcomePage")
        else:
            messagebox.showerror("Registration Error", "Email already registered!")

# Login page class
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Login", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="Email").pack()
        self.email_entry = tk.Entry(self)
        self.email_entry.pack()
        tk.Label(self, text="Password").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        tk.Button(self, text="Login", command=self.login_user).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("WelcomePage")).pack(pady=10)

    def login_user(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        success = self.controller.user_manager.login_user(email, password)
        if success:
            messagebox.showinfo("Login", "Logged in successfully!")
            self.controller.show_frame("ApplicationPage")
        else:
            messagebox.showerror("Login Error", "Invalid email or password!")

# Application page class
class ApplicationPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Application Page", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Profile Management", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)
        tk.Button(self, text="Social Media Scheduler", command=self.open_social_media_scheduler).pack(pady=10)

    def open_social_media_scheduler(self):
        # Placeholder for social media scheduler page
        pass

# Profile management page class
class ProfileManagementPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Profile Management", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Update Username", command=lambda: controller.show_frame("UpdateUsernamePage")).pack(pady=10)
        tk.Button(self, text="Update Email", command=lambda: controller.show_frame("UpdateEmailPage")).pack(pady=10)
        tk.Button(self, text="Change Password", command=lambda: controller.show_frame("ChangePasswordPage")).pack(pady=10)
        tk.Button(self, text="Logout", command=self.logout_user).pack(pady=10)
        tk.Button(self, text="Delete Account", command=self.delete_account).pack(pady=10)

    def logout_user(self):
        self.controller.user_manager.logout_user()
        self.controller.show_frame("WelcomePage")

    def delete_account(self):
        success = self.controller.user_manager.delete_account()
        if success:
            messagebox.showinfo("Delete Account", "Account deleted successfully!")
            self.controller.show_frame("WelcomePage")
        else:
            messagebox.showerror("Delete Error", "No account to delete!")

# Update username page class
class UpdateUsernamePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Update Username", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="New Username").pack()
        self.new_username_entry = tk.Entry(self)
        self.new_username_entry.pack()
        tk.Button(self, text="Update", command=self.update_username).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)

    def update_username(self):
        new_username = self.new_username_entry.get()
        success = self.controller.user_manager.update_username(new_username)
        if success:
            messagebox.showinfo("Update Username", f"Username updated to {new_username} successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            messagebox.showerror("Update Error", "Failed to update username!")

# Update email page class
class UpdateEmailPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Update Email", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="New Email").pack()
        self.new_email_entry = tk.Entry(self)
        self.new_email_entry.pack()
        tk.Button(self, text="Update", command=self.update_email).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)

    def update_email(self):
        new_email = self.new_email_entry.get()
        success = self.controller.user_manager.update_email(new_email)
        if success:
            messagebox.showinfo("Update Email", f"Email updated to {new_email} successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            messagebox.showerror("Update Error", "Email already in use or failed to update!")

# Change password page class
class ChangePasswordPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Change Password", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="Current Password").pack()
        self.current_password_entry = tk.Entry(self, show="*")
        self.current_password_entry.pack()
        tk.Label(self, text="New Password").pack()
        self.new_password_entry = tk.Entry(self, show="*")
        self.new_password_entry.pack()
        tk.Button(self, text="Update", command=self.change_password).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)

    def change_password(self):
        current_password = self.current_password_entry.get()
        new_password = self.new_password_entry.get()
        success = self.controller.user_manager.change_password(current_password, new_password)
        if success:
            messagebox.showinfo("Change Password", "Password changed successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            messagebox.showerror("Change Password Error", "Current password is incorrect!")

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
