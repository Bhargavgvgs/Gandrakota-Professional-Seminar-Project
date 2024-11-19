import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
import requests
import json

# User class to store individual user data
class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        self.instagram_access_token = None  # Store Instagram access token
        self.instagram_account_id = None    # Store Instagram Business Account ID
        self.drafts = []                    # List to store draft posts
        self.scheduled_posts = []           # List to store scheduled posts

# Post class to represent a social media post
class Post:
    def __init__(self, content, images=None, schedule_time=None):
        self.content = content
        self.images = images or []
        self.schedule_time = schedule_time
        self.status = 'draft'  # 'draft' or 'scheduled'

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
        self.title("Instagram Post Scheduler")
        self.user_manager = UserManager()
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        # Configure the grid
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Initialize frames dict
        self.frames = {}
        for F in (
            WelcomePage, RegisterPage, LoginPage, ApplicationPage,
            ProfileManagementPage, UpdateUsernamePage, UpdateEmailPage,
            ChangePasswordPage, SocialMediaSchedulerPage, InstagramAuthPage
        ):
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
        tk.Label(self, text="Welcome to Instagram Post Scheduler", font=("Arial", 16)).pack(pady=20)
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
        tk.Button(self, text="Instagram Scheduler", command=self.open_social_media_scheduler).pack(pady=10)

    def open_social_media_scheduler(self):
        user = self.controller.user_manager.current_user
        if user.instagram_access_token:
            self.controller.show_frame("SocialMediaSchedulerPage")
        else:
            self.controller.show_frame("InstagramAuthPage")

# Instagram authentication page class
class InstagramAuthPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        tk.Label(self, text="Connect Your Instagram Account", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Authenticate with Instagram", command=self.authenticate_instagram).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(pady=10)

    def authenticate_instagram(self):
        # Normally, you'd open a web browser for OAuth flow.
        # For simplicity, we'll ask for an access token directly.
        # In production, implement the full OAuth 2.0 flow.
        access_token = simpledialog.askstring("Instagram Access Token", "Enter your Instagram Access Token:")
        if access_token:
            user = self.controller.user_manager.current_user
            user.instagram_access_token = access_token
            # Get the Instagram Business Account ID
            success = self.get_instagram_account_id(user)
            if success:
                messagebox.showinfo("Authentication", "Instagram account connected successfully!")
                self.controller.show_frame("SocialMediaSchedulerPage")
            else:
                messagebox.showerror("Authentication Error", "Failed to retrieve Instagram Business Account ID.")

    def get_instagram_account_id(self, user):
        # Get the user's Facebook Pages
        url = "https://graph.facebook.com/v17.0/me/accounts"
        params = {
            "access_token": user.instagram_access_token
        }
        response = requests.get(url, params=params)
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            page_id = data['data'][0]['id']
            # Get the Instagram Business Account ID
            url = f"https://graph.facebook.com/v17.0/{page_id}"
            params = {
                "fields": "instagram_business_account",
                "access_token": user.instagram_access_token
            }
            response = requests.get(url, params=params)
            data = response.json()
            if 'instagram_business_account' in data:
                user.instagram_account_id = data['instagram_business_account']['id']
                return True
        return False

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

# Social media scheduler page class
class SocialMediaSchedulerPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Create a notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        # Create frames for each tab
        create_post_frame = CreatePostPage(notebook, controller)
        drafts_frame = DraftsPage(notebook, controller)
        scheduled_posts_frame = ScheduledPostsPage(notebook, controller)

        # Add frames to notebook
        notebook.add(create_post_frame, text='Create Post')
        notebook.add(drafts_frame, text='Drafts')
        notebook.add(scheduled_posts_frame, text='Scheduled Posts')

        # Add a back button to go back to ApplicationPage
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(pady=10)

# Create post page class
class CreatePostPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Build the page
        tk.Label(self, text="Create New Post", font=("Arial", 16)).pack(pady=10)

        # Content text field
        tk.Label(self, text="Content:").pack(anchor='w')
        self.content_text = tk.Text(self, height=10)
        self.content_text.pack(fill='x', padx=10)

        # Attach images/videos
        tk.Label(self, text="Attach Images (JPEG only):").pack(anchor='w')
        self.images = []  # list to store image file paths
        self.attach_button = tk.Button(self, text="Attach Image", command=self.attach_files)
        self.attach_button.pack()

        # Buttons
        tk.Button(self, text="Save as Draft", command=self.save_as_draft).pack(pady=5)
        tk.Button(self, text="Schedule Post", command=self.schedule_post).pack(pady=5)

    def attach_files(self):
        # Open file dialog to select images (JPEG only for Instagram)
        file = filedialog.askopenfilename(
            title="Select Image",
            filetypes=(
                ("JPEG Files", "*.jpg;*.jpeg"),
                ("All Files", "*.*")
            )
        )
        if file:
            self.images.append(file)
            messagebox.showinfo("File Attached", f"Image attached: {file}")

    def save_as_draft(self):
        content = self.content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty Content", "Please enter content for the post.")
            return
        if not self.images:
            messagebox.showwarning("No Image", "Please attach an image.")
            return
        # Create a Post object
        post = Post(content, images=self.images.copy())
        post.status = 'draft'
        # Add to user's drafts
        self.controller.user_manager.current_user.drafts.append(post)
        messagebox.showinfo("Draft Saved", "Post saved as draft successfully.")
        # Clear the form
        self.content_text.delete("1.0", tk.END)
        self.images = []

    def schedule_post(self):
        content = self.content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty Content", "Please enter content for the post.")
            return
        if not self.images:
            messagebox.showwarning("No Image", "Please attach an image.")
            return
        # Open a scheduling dialog
        schedule_dialog = ScheduleDialog(self.controller, self, content, self.images.copy())
        self.wait_window(schedule_dialog)
        # Clear the form if scheduling was successful
        if schedule_dialog.success:
            self.content_text.delete("1.0", tk.END)
            self.images = []

# Schedule dialog class
class ScheduleDialog(tk.Toplevel):
    def __init__(self, controller, parent, content, images):
        super().__init__(parent)
        self.title("Schedule Post")
        self.controller = controller
        self.success = False  # flag to check if scheduling was successful

        # Content of the post
        self.content = content
        self.images = images

        # Date and time selection
        tk.Label(self, text="Select Date and Time to Schedule").pack(pady=10)
        self.date_var = tk.StringVar()
        self.time_var = tk.StringVar()

        # Date picker
        tk.Label(self, text="Date (YYYY-MM-DD):").pack()
        self.date_entry = tk.Entry(self, textvariable=self.date_var)
        self.date_entry.pack()

        # Time picker
        tk.Label(self, text="Time (HH:MM):").pack()
        self.time_entry = tk.Entry(self, textvariable=self.time_var)
        self.time_entry.pack()

        # Buttons
        tk.Button(self, text="Schedule", command=self.schedule_post).pack(pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).pack()

    def schedule_post(self):
        date_str = self.date_var.get()
        time_str = self.time_var.get()
        if not date_str or not time_str:
            messagebox.showwarning("Invalid Input", "Please enter date and time.")
            return
        # Parse date and time
        try:
            schedule_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except Exception as e:
            messagebox.showerror("Invalid Date/Time", f"Error: {str(e)}")
            return
        # Create Post object
        post = Post(
            self.content,
            images=self.images,
            schedule_time=schedule_time
        )
        post.status = 'scheduled'
        # Add to user's scheduled posts
        self.controller.user_manager.current_user.scheduled_posts.append(post)
        messagebox.showinfo("Post Scheduled", "Post has been scheduled successfully.")
        self.success = True
        self.destroy()

# Drafts page class
class DraftsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        tk.Label(self, text="Drafts", font=("Arial", 16)).pack(pady=10)

        # Listbox to display drafts
        self.drafts_listbox = tk.Listbox(self)
        self.drafts_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        self.drafts_listbox.bind('<<ListboxSelect>>', self.on_draft_select)

        # Buttons
        tk.Button(self, text="Edit Draft", command=self.edit_draft).pack(pady=5)
        tk.Button(self, text="Delete Draft", command=self.delete_draft).pack(pady=5)

        self.refresh_drafts()

    def refresh_drafts(self):
        self.drafts_listbox.delete(0, tk.END)
        drafts = self.controller.user_manager.current_user.drafts
        for idx, draft in enumerate(drafts):
            self.drafts_listbox.insert(tk.END, f"Draft {idx+1}: {draft.content[:30]}...")

    def on_draft_select(self, event):
        # Get selected draft
        selection = self.drafts_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_draft = self.controller.user_manager.current_user.drafts[index]
        else:
            self.selected_draft = None

    def edit_draft(self):
        if hasattr(self, 'selected_draft') and self.selected_draft:
            # Open the EditDraftDialog
            edit_dialog = EditDraftDialog(self.controller, self, self.selected_draft)
            self.wait_window(edit_dialog)
            # Refresh the list after editing
            self.refresh_drafts()
        else:
            messagebox.showwarning("No Selection", "Please select a draft to edit.")

    def delete_draft(self):
        if hasattr(self, 'selected_draft') and self.selected_draft:
            confirm = messagebox.askyesno("Delete Draft", "Are you sure you want to delete this draft?")
            if confirm:
                self.controller.user_manager.current_user.drafts.remove(self.selected_draft)
                self.refresh_drafts()
                messagebox.showinfo("Draft Deleted", "Draft has been deleted.")
        else:
            messagebox.showwarning("No Selection", "Please select a draft to delete.")

# Edit draft dialog class
class EditDraftDialog(tk.Toplevel):
    def __init__(self, controller, parent, draft):
        super().__init__(parent)
        self.title("Edit Draft")
        self.controller = controller
        self.draft = draft

        # Build the page similar to CreatePostPage
        tk.Label(self, text="Edit Draft", font=("Arial", 16)).pack(pady=10)

        # Content text field
        tk.Label(self, text="Content:").pack(anchor='w')
        self.content_text = tk.Text(self, height=10)
        self.content_text.pack(fill='x', padx=10)
        self.content_text.insert("1.0", self.draft.content)

        # Attached images
        tk.Label(self, text="Attached Images (JPEG only):").pack(anchor='w')
        self.images = self.draft.images.copy()
        self.attach_button = tk.Button(self, text="Attach Image", command=self.attach_files)
        self.attach_button.pack()

        # Buttons
        tk.Button(self, text="Save Changes", command=self.save_changes).pack(pady=5)
        tk.Button(self, text="Cancel", command=self.destroy).pack(pady=5)

    def attach_files(self):
        # Open file dialog to select images (JPEG only for Instagram)
        file = filedialog.askopenfilename(
            title="Select Image",
            filetypes=(
                ("JPEG Files", "*.jpg;*.jpeg"),
                ("All Files", "*.*")
            )
        )
        if file:
            self.images.append(file)
            messagebox.showinfo("File Attached", f"Image attached: {file}")

    def save_changes(self):
        content = self.content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty Content", "Please enter content for the post.")
            return
        if not self.images:
            messagebox.showwarning("No Image", "Please attach an image.")
            return
        # Update the draft
        self.draft.content = content
        self.draft.images = self.images.copy()
        messagebox.showinfo("Draft Updated", "Draft has been updated successfully.")
        self.destroy()

# Scheduled posts page class
class ScheduledPostsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        tk.Label(self, text="Scheduled Posts", font=("Arial", 16)).pack(pady=10)

        # Listbox to display scheduled posts
        self.scheduled_listbox = tk.Listbox(self)
        self.scheduled_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        self.scheduled_listbox.bind('<<ListboxSelect>>', self.on_post_select)

        # Buttons
        tk.Button(self, text="Edit Scheduled Post", command=self.edit_post).pack(pady=5)
        tk.Button(self, text="Delete Scheduled Post", command=self.delete_post).pack(pady=5)
        tk.Button(self, text="Post Now", command=self.post_now).pack(pady=5)

        self.refresh_scheduled_posts()

    def refresh_scheduled_posts(self):
        self.scheduled_listbox.delete(0, tk.END)
        scheduled_posts = self.controller.user_manager.current_user.scheduled_posts
        for idx, post in enumerate(scheduled_posts):
            schedule_time_str = post.schedule_time.strftime("%Y-%m-%d %H:%M")
            self.scheduled_listbox.insert(tk.END, f"Post {idx+1}: {post.content[:30]}... Scheduled for {schedule_time_str}")

    def on_post_select(self, event):
        # Get selected post
        selection = self.scheduled_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_post = self.controller.user_manager.current_user.scheduled_posts[index]
        else:
            self.selected_post = None

    def edit_post(self):
        if hasattr(self, 'selected_post') and self.selected_post:
            # Open the EditScheduledPostDialog
            edit_dialog = EditScheduledPostDialog(self.controller, self, self.selected_post)
            self.wait_window(edit_dialog)
            # Refresh the list after editing
            self.refresh_scheduled_posts()
        else:
            messagebox.showwarning("No Selection", "Please select a scheduled post to edit.")

    def delete_post(self):
        if hasattr(self, 'selected_post') and self.selected_post:
            confirm = messagebox.askyesno("Delete Scheduled Post", "Are you sure you want to delete this scheduled post?")
            if confirm:
                self.controller.user_manager.current_user.scheduled_posts.remove(self.selected_post)
                self.refresh_scheduled_posts()
                messagebox.showinfo("Scheduled Post Deleted", "Scheduled post has been deleted.")
        else:
            messagebox.showwarning("No Selection", "Please select a scheduled post to delete.")

    def post_now(self):
        if hasattr(self, 'selected_post') and self.selected_post:
            confirm = messagebox.askyesno("Post Now", "Are you sure you want to post this now?")
            if confirm:
                # Call the method to post to Instagram
                success = self.post_to_instagram(self.selected_post)
                if success:
                    self.controller.user_manager.current_user.scheduled_posts.remove(self.selected_post)
                    self.refresh_scheduled_posts()
                    messagebox.showinfo("Post Successful", "Post has been published to Instagram.")
                else:
                    messagebox.showerror("Post Failed", "Failed to post to Instagram.")
        else:
            messagebox.showwarning("No Selection", "Please select a scheduled post to publish.")

    def post_to_instagram(self, post):
        user = self.controller.user_manager.current_user
        if not user.instagram_access_token or not user.instagram_account_id:
            messagebox.showerror("Instagram Not Connected", "Please connect your Instagram account.")
            return False

        # Step 1: Upload the image
        upload_url = f"https://graph.facebook.com/v17.0/{user.instagram_account_id}/media"
        image_path = post.images[0]  # Instagram only supports one image per post via API
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        files = {
            'image_file': (image_path, image_data, 'image/jpeg')
        }
        payload = {
            'caption': post.content,
            'access_token': user.instagram_access_token
        }
        response = requests.post(upload_url, data=payload, files=files)
        result = response.json()
        if 'id' in result:
            creation_id = result['id']
            # Step 2: Publish the media
            publish_url = f"https://graph.facebook.com/v17.0/{user.instagram_account_id}/media_publish"
            payload = {
                'creation_id': creation_id,
                'access_token': user.instagram_access_token
            }
            response = requests.post(publish_url, data=payload)
            result = response.json()
            if 'id' in result:
                return True
        return False

# Edit scheduled post dialog class
class EditScheduledPostDialog(tk.Toplevel):
    def __init__(self, controller, parent, post):
        super().__init__(parent)
        self.title("Edit Scheduled Post")
        self.controller = controller
        self.post = post

        # Build the page similar to CreatePostPage and ScheduleDialog
        tk.Label(self, text="Edit Scheduled Post", font=("Arial", 16)).pack(pady=10)

        # Content text field
        tk.Label(self, text="Content:").pack(anchor='w')
        self.content_text = tk.Text(self, height=10)
        self.content_text.pack(fill='x', padx=10)
        self.content_text.insert("1.0", self.post.content)

        # Attached images
        tk.Label(self, text="Attached Images (JPEG only):").pack(anchor='w')
        self.images = self.post.images.copy()
        self.attach_button = tk.Button(self, text="Attach Image", command=self.attach_files)
        self.attach_button.pack()

        # Date and time selection
        tk.Label(self, text="Scheduled Date and Time").pack(pady=10)
        self.date_var = tk.StringVar(value=self.post.schedule_time.strftime("%Y-%m-%d"))
        self.time_var = tk.StringVar(value=self.post.schedule_time.strftime("%H:%M"))

        # Date picker
        tk.Label(self, text="Date (YYYY-MM-DD):").pack()
        self.date_entry = tk.Entry(self, textvariable=self.date_var)
        self.date_entry.pack()

        # Time picker
        tk.Label(self, text="Time (HH:MM):").pack()
        self.time_entry = tk.Entry(self, textvariable=self.time_var)
        self.time_entry.pack()

        # Buttons
        tk.Button(self, text="Save Changes", command=self.save_changes).pack(pady=5)
        tk.Button(self, text="Cancel", command=self.destroy).pack(pady=5)

    def attach_files(self):
        # Open file dialog to select images (JPEG only for Instagram)
        file = filedialog.askopenfilename(
            title="Select Image",
            filetypes=(
                ("JPEG Files", "*.jpg;*.jpeg"),
                ("All Files", "*.*")
            )
        )
        if file:
            self.images.append(file)
            messagebox.showinfo("File Attached", f"Image attached: {file}")

    def save_changes(self):
        content = self.content_text.get("1.0", tk.END).strip()
        date_str = self.date_var.get()
        time_str = self.time_var.get()
        if not content:
            messagebox.showwarning("Empty Content", "Please enter content for the post.")
            return
        if not self.images:
            messagebox.showwarning("No Image", "Please attach an image.")
            return
        if not date_str or not time_str:
            messagebox.showwarning("Invalid Input", "Please enter date and time.")
            return
        # Parse date and time
        try:
            schedule_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except Exception as e:
            messagebox.showerror("Invalid Date/Time", f"Error: {str(e)}")
            return
        # Update the post
        self.post.content = content
        self.post.images = self.images.copy()
        self.post.schedule_time = schedule_time
        messagebox.showinfo("Scheduled Post Updated", "Scheduled post has been updated successfully.")
        self.destroy()

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
