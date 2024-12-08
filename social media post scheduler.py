import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime, timedelta
import requests
import threading
import time
import os
import json
from dotenv import load_dotenv
from instabot import Bot
import queue
import logging
import glob
import pytz
from tkcalendar import Calendar

# Load environment variables from .env file
load_dotenv()

# -------------------- Logging Configuration -------------------- #
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs if needed
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# -------------------- User Classes -------------------- #

# Post class to store individual post data
class Post:
    def __init__(self, content, media_files, platforms):
        self.content = content
        self.media_files = media_files  # List of file paths
        self.platforms = platforms      # List of selected platforms

    def to_dict(self):
        return {
            'content': self.content,
            'media_files': self.media_files,
            'platforms': self.platforms
        }

    @staticmethod
    def from_dict(data):
        return Post(data.get('content', ''), data.get('media_files', []), data.get('platforms', []))

# ScheduledPost class to store scheduled posts
class ScheduledPost:
    def __init__(self, post, platform, scheduled_time, timezone, recurrence=None):
        self.post = post
        self.platform = platform
        self.scheduled_time = scheduled_time  # datetime object with timezone
        self.timezone = timezone
        self.recurrence = recurrence  # e.g., 'Daily', 'Weekly', 'Monthly'

    def to_dict(self):
        return {
            'post': self.post.to_dict(),
            'platform': self.platform,
            'scheduled_time': self.scheduled_time.isoformat(),
            'timezone': self.timezone,
            'recurrence': self.recurrence
        }

    @staticmethod
    def from_dict(data):
        post = Post.from_dict(data.get('post', {}))
        scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        return ScheduledPost(
            post,
            data.get('platform', ''),
            scheduled_time,
            data.get('timezone', ''),
            data.get('recurrence', None)
        )

# User class to store individual user data
class User:
    def __init__(self, name, email, password, drafts=None):
        self.name = name
        self.email = email
        self.password = password
        self.drafts = drafts if drafts is not None else []  # List of Post objects

    def add_draft(self, post):
        self.drafts.append(post)

    def delete_draft(self, index):
        if 0 <= index < len(self.drafts):
            del self.drafts[index]

    def get_drafts(self):
        return self.drafts

    def update_draft(self, index, post):
        if 0 <= index < len(self.drafts):
            self.drafts[index] = post

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'drafts': [draft.to_dict() for draft in self.drafts]
        }

    @staticmethod
    def from_dict(data):
        drafts = [Post.from_dict(draft) for draft in data.get('drafts', [])]
        return User(data['name'], data['email'], data['password'], drafts)

# UserManager class to handle user data storage and operations
class UserManager:
    def __init__(self, filepath='users.json'):
        self.filepath = filepath
        self.users = {}  # key: email, value: User object
        self.current_user = None
        self.load_users()

    def load_users(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    for email, user_data in data.items():
                        self.users[email] = User.from_dict(user_data)
                logging.info("Users loaded successfully.")
            except Exception as e:
                logging.error(f"Error loading users: {e}")
                messagebox.showerror("Load Error", f"Failed to load user data:\n{e}")

    def save_users(self):
        try:
            data = {email: user.to_dict() for email, user in self.users.items()}
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=4)
            logging.info("Users saved successfully.")
        except Exception as e:
            logging.error(f"Error saving users: {e}")
            messagebox.showerror("Save Error", f"Failed to save user data:\n{e}")

    def register_user(self, name, email, password):
        if email in self.users:
            logging.warning(f"Registration failed: Email {email} already registered.")
            return False  # Registration failed
        else:
            self.users[email] = User(name, email, password)
            self.save_users()
            logging.info(f"User {email} registered successfully.")
            return True  # Registration successful

    def login_user(self, email, password):
        if email in self.users and self.users[email].password == password:
            self.current_user = self.users[email]
            logging.info(f"User {email} logged in successfully.")
            return True
        else:
            logging.warning(f"Login failed for {email}.")
            return False

    def logout_user(self):
        if self.current_user:
            logging.info(f"User {self.current_user.email} logged out.")
        self.current_user = None

    def delete_account(self):
        if self.current_user:
            del self.users[self.current_user.email]
            self.save_users()
            logging.info(f"User {self.current_user.email} deleted their account.")
            self.current_user = None
            return True
        else:
            logging.warning("Delete account failed: No user is currently logged in.")
            return False

    def update_username(self, new_username):
        if self.current_user:
            old_username = self.current_user.name
            self.current_user.name = new_username
            self.save_users()
            logging.info(f"User {self.current_user.email} updated username from {old_username} to {new_username}.")
            return True
        else:
            logging.warning("Update username failed: No user is currently logged in.")
            return False

    def update_email(self, new_email):
        if new_email in self.users:
            logging.warning(f"Update email failed: Email {new_email} already in use.")
            return False  # Email already in use
        else:
            if self.current_user:
                old_email = self.current_user.email
                self.users[new_email] = self.users.pop(self.current_user.email)
                self.current_user.email = new_email
                self.save_users()
                logging.info(f"User updated email from {old_email} to {new_email}.")
                return True
            else:
                logging.warning("Update email failed: No user is currently logged in.")
                return False

    def change_password(self, current_password, new_password):
        if self.current_user and self.current_user.password == current_password:
            self.current_user.password = new_password
            self.save_users()
            logging.info(f"User {self.current_user.email} changed their password successfully.")
            return True
        else:
            logging.warning("Change password failed: Incorrect current password or no user logged in.")
            return False

# -------------------- API Posting Function -------------------- #

# Load Instagram credentials from environment variables
# INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
# INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Initialize Instabot for Instagram
INSTAGRAM_USERNAME = 'mailid4learning@gmail.com'
INSTAGRAM_PASSWORD = 'BHARGAV1234'

# Hard-coded Access Tokens and IDs for Facebook (As per your request)
FACEBOOK_ACCESS_TOKEN = 'EAASbOH6aOncBOwwC0HfJQqgRWoTBbZA8amhy6SITcpFrUreMMkuwvNdtRkaW1mqZAyznJBfDIEU27CaMNnnOGpqZBpVtsG6T0NGUtuENiEjIahrJUPs7B0GCP6o8Xv15e01Frqp1ZBgpHuipd3E9FjaSMZBLlMihXNPrUng8ZBQpaZBEzCUPNsu46PwJjc5yGz0YUprxNdM'
FACEBOOK_PAGE_ID = '475462135656006'

# Initialize Instabot for Instagram
# Initialize the Instabot only once
insta_bot = None
insta_bot_lock = threading.Lock()

def initialize_instabot():
    global insta_bot
    with insta_bot_lock:
        if insta_bot is None:
            config_dir = 'config'  # Default Instabot config directory
            cookies_pattern = os.path.join(config_dir, '*cookie.json')
            cookie_files = glob.glob(cookies_pattern)
            
            # Delete all existing cookies.json files
            for cookie_file in cookie_files:
                try:
                    os.remove(cookie_file)
                    logging.info(f"Deleted cookie file: {cookie_file}")
                except Exception as e:
                    logging.error(f"Failed to delete cookie file {cookie_file}: {e}")
                    messagebox.showerror("Cookie Deletion Error", f"Failed to delete existing cookie {cookie_file}:\n{e}")
            
            # Initialize Instabot
            insta_bot = Bot()
            try:
                insta_bot.login(username=INSTAGRAM_USERNAME, password=INSTAGRAM_PASSWORD)
                logging.info("Instabot logged in successfully.")
            except Exception as e:
                logging.error(f"Failed to login to Instagram: {e}")
                messagebox.showerror("Instagram Login Error", f"Failed to login to Instagram:\n{e}")
                insta_bot = None

# Queue for Instagram posts to ensure they run in the main thread
instagram_queue = queue.Queue()

def process_instagram_queue(app):
    while not instagram_queue.empty():
        post = instagram_queue.get()
        try:
            if not post.media_files:
                logging.error("Instagram Post Error: No media file selected for Instagram post.")
                messagebox.showerror("Instagram Post Error", "No media file selected for Instagram post.")
                continue

            media_file = post.media_files[0]
            original_extension = os.path.splitext(media_file)[1]
            temp_photo = os.path.splitext(media_file)[0] + "_temp" + original_extension

            # Initialize Instabot and login
            initialize_instabot()
            if insta_bot is None:
                continue  # Initialization failed

            # Post based on media type
            if original_extension.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                try:
                    # Rename the photo with "_temp" suffix
                    os.rename(media_file, temp_photo)
                    logging.debug(f"Renamed {media_file} to {temp_photo}")
                except Exception as e:
                    logging.error(f"Error renaming media file: {e}")
                    messagebox.showerror("Instagram Post Error", f"Error processing media file:\n{e}")
                    continue

                try:
                    insta_bot.upload_photo(temp_photo, caption=post.content)
                    logging.info(f"Photo '{media_file}' uploaded to Instagram.")
                    messagebox.showinfo("Post Success", "Successfully posted to Instagram.")
                except Exception as e:
                    logging.error(f"Failed to upload photo to Instagram: {e}")
                    messagebox.showerror("Instagram Post Error", f"Failed to upload photo:\n{e}")
                finally:
                    # Rename back after upload
                    try:
                        os.rename(temp_photo, media_file)
                        logging.debug(f"Renamed {temp_photo} back to {media_file}")
                    except Exception as e:
                        logging.error(f"Error reverting media file name: {e}")

            elif original_extension.lower() in ['.mp4', '.avi', '.mov']:
                try:
                    insta_bot.upload_video(media_file, caption=post.content)
                    logging.info(f"Video '{media_file}' uploaded to Instagram.")
                    messagebox.showinfo("Post Success", "Successfully posted to Instagram.")
                except Exception as e:
                    logging.error(f"Failed to upload video to Instagram: {e}")
                    messagebox.showerror("Instagram Post Error", f"Failed to upload video:\n{e}")
            else:
                logging.error("Unsupported media type for Instagram.")
                messagebox.showerror("Instagram Post Error", "Unsupported media type for Instagram.")
        except Exception as e:
            logging.error(f"Exception during Instagram posting: {e}")
            messagebox.showerror("Instagram Post Error", f"Exception: {e}")
        finally:
            instagram_queue.task_done()

def post_to_social_media(app, post, platform):
    # Headers for JSON content
    headers = {
        "Content-Type": "application/json"
    }

    # Post to Facebook
    if platform == 'Facebook':
        try:
            if post.media_files:
                # For media posts
                media_file = post.media_files[0]
                if media_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Photo upload
                    url = f"https://graph.facebook.com/v21.0/{FACEBOOK_PAGE_ID}/photos"
                    with open(media_file, 'rb') as f:
                        files = {'source': f}
                        data = {
                            'caption': post.content,
                            'access_token': FACEBOOK_ACCESS_TOKEN
                        }
                        response = requests.post(url, data=data, files=files)
                else:
                    # Video upload
                    url = f"https://graph.facebook.com/v21.0/{FACEBOOK_PAGE_ID}/videos"
                    with open(media_file, 'rb') as f:
                        files = {'source': f}
                        data = {
                            'description': post.content,
                            'access_token': FACEBOOK_ACCESS_TOKEN
                        }
                        response = requests.post(url, data=data, files=files)
            else:
                # Text post
                url = f"https://graph.facebook.com/v21.0/{FACEBOOK_PAGE_ID}/feed"
                payload = {
                    "message": post.content,
                    "access_token": FACEBOOK_ACCESS_TOKEN
                }
                response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logging.info('Successfully posted to Facebook.')
                messagebox.showinfo("Post Success", "Successfully posted to Facebook.")
                app.notification_log.add_notification(f"Posted to Facebook at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                logging.error(f'Failed to post to Facebook: {response.text}')
                messagebox.showerror("Facebook Post Error", f"Failed to post to Facebook:\n{response.text}")
                app.notification_log.add_notification(f"Failed to post to Facebook at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logging.error(f'Exception during Facebook posting: {e}')
            messagebox.showerror("Facebook Post Error", f"Exception: {e}")
            app.notification_log.add_notification(f"Exception while posting to Facebook at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")

    # Post to Instagram using Instabot via queue
    elif platform == 'Instagram':
        try:
            if not post.media_files:
                logging.error("Instagram Post Error: No media file selected for Instagram post.")
                messagebox.showerror("Instagram Post Error", "No media file selected for Instagram post.")
                app.notification_log.add_notification("Instagram post failed: No media file selected.")
                return

            # Enqueue the post to be processed in the main thread
            instagram_queue.put(post)
            # Trigger the queue processing in the main thread
            app.after(0, lambda: process_instagram_queue(app))
            logging.info("Instagram post enqueued successfully.")
            app.notification_log.add_notification(f"Instagram post enqueued at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logging.error(f'Exception during Instagram posting: {e}')
            messagebox.showerror("Instagram Post Error", f"Exception: {e}")
            app.notification_log.add_notification(f"Exception while posting to Instagram at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {e}")

# -------------------- Scheduler Function -------------------- #

def schedule_checker(app):
    while True:
        now = datetime.now(pytz.utc)
        for scheduled_post in app.scheduled_posts[:]:
            post_time_utc = scheduled_post.scheduled_time.astimezone(pytz.utc)
            if now >= post_time_utc:
                post_to_social_media(app, scheduled_post.post, scheduled_post.platform)
                app.scheduled_posts.remove(scheduled_post)
                app.notification_log.add_notification(f"Post published on {scheduled_post.platform}.")
                logging.info(f"Post published on {scheduled_post.platform}.")
                # Handle recurrence
                if scheduled_post.recurrence:
                    next_time = get_next_recurrence_time(scheduled_post.scheduled_time, scheduled_post.recurrence)
                    if next_time:
                        new_scheduled_post = ScheduledPost(
                            scheduled_post.post,
                            scheduled_post.platform,
                            next_time,
                            scheduled_post.timezone,
                            scheduled_post.recurrence
                        )
                        app.scheduled_posts.append(new_scheduled_post)
                        app.notification_log.add_notification(f"Recurring post scheduled for {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        logging.info(f"Recurring post scheduled for {next_time.strftime('%Y-%m-%d %H:%M:%S')}.")
        time.sleep(60)  # Check every minute

def get_next_recurrence_time(current_time, recurrence):
    if recurrence == 'Daily':
        return current_time + timedelta(days=1)
    elif recurrence == 'Weekly':
        return current_time + timedelta(weeks=1)
    elif recurrence == 'Monthly':
        # Simple approach: add 30 days
        return current_time + timedelta(days=30)
    else:
        return None

# -------------------- Notification Log Class -------------------- #

class NotificationLog:
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
        self.enabled = tk.BooleanVar(value=True)
        self.create_widgets()

    def create_widgets(self):
        # Since NotificationLogPage handles the display, this can be minimal
        pass

    def add_notification(self, message):
        if self.enabled.get():
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            notification = f"{timestamp}: {message}"
            self.notifications.append(notification)
            logging.info(f"Notification added: {notification}")

    def clear_log(self):
        self.notifications.clear()
        logging.info("Notification log cleared.")

# -------------------- Main Application Class -------------------- #

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Social Media Post Scheduler")
        self.geometry("800x800")
        self.user_manager = UserManager()
        self.scheduled_posts = []  # List of ScheduledPost objects
        self.notification_log = NotificationLog(self)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        # Configure the grid
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Initialize frames dict
        self.frames = {}
        for F in (WelcomePage, RegisterPage, LoginPage, ApplicationPage, ProfileManagementPage,
                  UpdateUsernamePage, UpdateEmailPage, ChangePasswordPage,
                  NewPostPage, DraftsPage, EditDraftPage, SchedulePostPage, ViewScheduledPostsPage, NotificationLogPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            # Put all pages in the same location;
            # The one on the top of the stacking order
            # will be the one that is visible
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("WelcomePage")

        # Start the scheduler thread
        scheduler_thread = threading.Thread(target=schedule_checker, args=(self,), daemon=True)
        scheduler_thread.start()
        logging.info("Scheduler thread started.")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

# -------------------- Page Classes -------------------- #

# Welcome page class
class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Welcome to Social Media Post Scheduler", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Login", command=lambda: controller.show_frame("LoginPage")).pack(pady=10)
        tk.Button(self, text="Register", command=lambda: controller.show_frame("RegisterPage")).pack(pady=10)

# Register page class
class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
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
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not name or not email or not password:
            messagebox.showerror("Registration Error", "All fields are required!")
            return
        success = self.controller.user_manager.register_user(name, email, password)
        if success:
            logging.info("User registered successfully.")
            messagebox.showinfo("Registration", "User registered successfully!")
            self.controller.show_frame("WelcomePage")
        else:
            logging.warning("Registration failed: Email already registered.")
            messagebox.showerror("Registration Error", "Email already registered!")

# Login page class
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
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
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            messagebox.showerror("Login Error", "Both fields are required!")
            return
        success = self.controller.user_manager.login_user(email, password)
        if success:
            logging.info(f"User {email} logged in successfully.")
            messagebox.showinfo("Login", "Logged in successfully!")
            self.controller.show_frame("ApplicationPage")
        else:
            logging.warning(f"Login failed for {email}.")
            messagebox.showerror("Login Error", "Invalid email or password!")

# Application page class
class ApplicationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Application Page", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Create New Post", command=lambda: controller.show_frame("NewPostPage")).pack(pady=10)
        tk.Button(self, text="View Drafts", command=lambda: controller.show_frame("DraftsPage")).pack(pady=10)
        tk.Button(self, text="Schedule Post", command=lambda: controller.show_frame("SchedulePostPage")).pack(pady=10)
        tk.Button(self, text="View Scheduled Posts", command=lambda: controller.show_frame("ViewScheduledPostsPage")).pack(pady=10)
        tk.Button(self, text="Profile Management", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)
        tk.Button(self, text="View Notification Log", command=lambda: controller.show_frame("NotificationLogPage")).pack(pady=10)

# NewPostPage class
class NewPostPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.media_files = []  # List of selected media file paths
        self.selected_platforms = []

        # Build the page
        tk.Label(self, text="Create New Post", font=("Arial", 16)).pack(pady=20)

        # Content text area
        tk.Label(self, text="Content").pack()
        self.content_text = tk.Text(self, height=10, width=60)
        self.content_text.pack()

        # Add media files
        tk.Button(self, text="Add Media Files", command=self.add_media_files).pack(pady=10)
        self.media_files_label = tk.Label(self, text="No media files selected")
        self.media_files_label.pack()

        # Select platforms
        tk.Label(self, text="Select Platforms").pack()
        self.platform_vars = {
            'Facebook': tk.IntVar(),
            'Instagram': tk.IntVar(),
            # 'Twitter': tk.IntVar()  # Uncomment if integrating Twitter later
        }
        for platform, var in self.platform_vars.items():
            tk.Checkbutton(self, text=platform, variable=var).pack(anchor='w')

        # Buttons
        tk.Button(self, text="Save Draft", command=self.save_draft).pack(pady=10)
        tk.Button(self, text="Post Now", command=self.post_now).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(pady=10)

    def add_media_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Media Files",
                                                 filetypes=[("Image and Video Files", "*.png;*.jpg;*.jpeg;*.gif;*.mp4;*.avi;*.mov")])
        if file_paths:
            self.media_files.extend(file_paths)
            self.media_files_label.config(text=f"{len(self.media_files)} media files selected")

    def save_draft(self):
        content = self.content_text.get("1.0", tk.END).strip()
        platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        if not content and not self.media_files:
            messagebox.showerror("Save Draft Error", "Content or media files required!")
            return
        if not platforms:
            messagebox.showerror("Save Draft Error", "Please select at least one platform!")
            return
        post = Post(content, self.media_files.copy(), platforms)
        self.controller.user_manager.current_user.add_draft(post)
        self.controller.user_manager.save_users()
        logging.info("Draft saved successfully.")
        messagebox.showinfo("Save Draft", "Draft saved successfully!")
        # Clear the form
        self.content_text.delete("1.0", tk.END)
        self.media_files = []
        self.media_files_label.config(text="No media files selected")
        for var in self.platform_vars.values():
            var.set(0)
        self.controller.show_frame("ApplicationPage")

    def post_now(self):
        content = self.content_text.get("1.0", tk.END).strip()
        platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        if not content and not self.media_files:
            messagebox.showerror("Post Now Error", "Content or media files required!")
            return
        if not platforms:
            messagebox.showerror("Post Now Error", "Please select at least one platform!")
            return
        post = Post(content, self.media_files.copy(), platforms)
        for platform in post.platforms:
            post_to_social_media(self.controller, post, platform)
        messagebox.showinfo("Post Now", "Post published successfully!")
        logging.info("Post published successfully.")
        # Clear the form
        self.content_text.delete("1.0", tk.END)
        self.media_files = []
        self.media_files_label.config(text="No media files selected")
        for var in self.platform_vars.values():
            var.set(0)
        self.controller.show_frame("ApplicationPage")

# DraftsPage class
class DraftsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Build the page
        tk.Label(self, text="Saved Drafts", font=("Arial", 16)).pack(pady=20)

        # Listbox to display drafts
        self.drafts_listbox = tk.Listbox(self, width=80)
        self.drafts_listbox.pack(fill=tk.BOTH, expand=True)
        self.drafts_listbox.bind('<Double-Button-1>', self.edit_draft)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Edit Draft", command=self.edit_draft_button).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Draft", command=self.delete_draft).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Post Selected", command=self.post_selected_draft).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Schedule Selected", command=self.schedule_selected_draft).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(side=tk.LEFT, padx=5)

    def update_drafts_list(self):
        self.drafts_listbox.delete(0, tk.END)
        drafts = self.controller.user_manager.current_user.get_drafts()
        for idx, draft in enumerate(drafts):
            platforms = ', '.join(draft.platforms)
            media_count = len(draft.media_files)
            display_text = f"Draft {idx+1}: Platforms: {platforms} | Media Files: {media_count} | Content: {draft.content[:30]}..."
            self.drafts_listbox.insert(tk.END, display_text)

    def edit_draft_button(self):
        selected = self.drafts_listbox.curselection()
        if selected:
            index = selected[0]
            self.controller.frames['EditDraftPage'].load_draft(index)
            self.controller.show_frame('EditDraftPage')
        else:
            messagebox.showerror("Edit Draft Error", "Please select a draft to edit.")

    def edit_draft(self, event):
        self.edit_draft_button()

    def delete_draft(self):
        selected = self.drafts_listbox.curselection()
        if selected:
            index = selected[0]
            confirm = messagebox.askyesno("Delete Draft", "Are you sure you want to delete this draft?")
            if confirm:
                self.controller.user_manager.current_user.delete_draft(index)
                self.controller.user_manager.save_users()
                self.update_drafts_list()
                logging.info(f"Draft {index+1} deleted successfully.")
                messagebox.showinfo("Delete Draft", "Draft deleted successfully!")
        else:
            messagebox.showerror("Delete Draft Error", "Please select a draft to delete.")

    def post_selected_draft(self):
        selected = self.drafts_listbox.curselection()
        if selected:
            index = selected[0]
            draft = self.controller.user_manager.current_user.drafts[index]
            for platform in draft.platforms:
                post_to_social_media(self.controller, draft, platform)
            logging.info(f"Draft {index+1} posted successfully.")
            messagebox.showinfo("Post Success", "Selected draft has been posted successfully!")
            # Optionally, remove the draft after posting
            # self.controller.user_manager.current_user.delete_draft(index)
            # self.controller.user_manager.save_users()
            # self.update_drafts_list()
        else:
            messagebox.showerror("Post Error", "Please select a draft to post.")

    def schedule_selected_draft(self):
        selected = self.drafts_listbox.curselection()
        if selected:
            index = selected[0]
            draft = self.controller.user_manager.current_user.drafts[index]
            # Pre-fill the scheduling form with draft data
            schedule_page = self.controller.frames['SchedulePostPage']
            schedule_page.load_from_draft(draft)
            self.controller.show_frame('SchedulePostPage')
        else:
            messagebox.showerror("Schedule Draft Error", "Please select a draft to schedule.")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_drafts_list()

# EditDraftPage class
class EditDraftPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.media_files = []  # List of selected media file paths
        self.selected_platforms = []
        self.draft_index = None  # Index of the draft being edited

        # Build the page
        tk.Label(self, text="Edit Draft", font=("Arial", 16)).pack(pady=20)

        # Content text area
        tk.Label(self, text="Content").pack()
        self.content_text = tk.Text(self, height=10, width=60)
        self.content_text.pack()

        # Add media files
        tk.Button(self, text="Add Media Files", command=self.add_media_files).pack(pady=10)
        self.media_files_label = tk.Label(self, text="No media files selected")
        self.media_files_label.pack()

        # Select platforms
        tk.Label(self, text="Select Platforms").pack()
        self.platform_vars = {
            'Facebook': tk.IntVar(),
            'Instagram': tk.IntVar(),
            # 'Twitter': tk.IntVar()  # Uncomment if integrating Twitter later
        }
        for platform, var in self.platform_vars.items():
            tk.Checkbutton(self, text=platform, variable=var).pack(anchor='w')

        # Buttons
        tk.Button(self, text="Save Changes", command=self.save_changes).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("DraftsPage")).pack(pady=10)

    def load_draft(self, index):
        self.draft_index = index
        draft = self.controller.user_manager.current_user.drafts[index]
        # Load content
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert(tk.END, draft.content)
        # Load media files
        self.media_files = draft.media_files.copy()
        if self.media_files:
            self.media_files_label.config(text=f"{len(self.media_files)} media files selected")
        else:
            self.media_files_label.config(text="No media files selected")
        # Load platforms
        for var in self.platform_vars.values():
            var.set(0)
        for platform in draft.platforms:
            if platform in self.platform_vars:
                self.platform_vars[platform].set(1)

    def add_media_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Media Files",
                                                 filetypes=[("Image and Video Files", "*.png;*.jpg;*.jpeg;*.gif;*.mp4;*.avi;*.mov")])
        if file_paths:
            self.media_files.extend(file_paths)
            self.media_files_label.config(text=f"{len(self.media_files)} media files selected")

    def save_changes(self):
        content = self.content_text.get("1.0", tk.END).strip()
        platforms = [platform for platform, var in self.platform_vars.items() if var.get()]
        if not content and not self.media_files:
            messagebox.showerror("Save Changes Error", "Content or media files required!")
            return
        if not platforms:
            messagebox.showerror("Save Changes Error", "Please select at least one platform!")
            return
        post = Post(content, self.media_files.copy(), platforms)
        self.controller.user_manager.current_user.update_draft(self.draft_index, post)
        self.controller.user_manager.save_users()
        logging.info(f"Draft {self.draft_index+1} updated successfully.")
        messagebox.showinfo("Save Changes", "Draft updated successfully!")
        self.controller.show_frame("DraftsPage")

# ProfileManagementPage class
class ProfileManagementPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
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
        logging.info("User logged out.")
        self.controller.show_frame("WelcomePage")

    def delete_account(self):
        confirm = messagebox.askyesno("Delete Account", "Are you sure you want to delete your account?")
        if confirm:
            success = self.controller.user_manager.delete_account()
            if success:
                logging.info("User account deleted successfully.")
                messagebox.showinfo("Delete Account", "Account deleted successfully!")
                self.controller.show_frame("WelcomePage")
            else:
                logging.error("Delete account failed: No account to delete.")
                messagebox.showerror("Delete Error", "No account to delete!")

# UpdateUsernamePage class
class UpdateUsernamePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Update Username", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="New Username").pack()
        self.new_username_entry = tk.Entry(self)
        self.new_username_entry.pack()
        tk.Button(self, text="Update", command=self.update_username).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)

    def update_username(self):
        new_username = self.new_username_entry.get().strip()
        if not new_username:
            messagebox.showerror("Update Error", "Username cannot be empty!")
            return
        success = self.controller.user_manager.update_username(new_username)
        if success:
            logging.info(f"Username updated to {new_username}.")
            messagebox.showinfo("Update Username", f"Username updated to {new_username} successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            logging.error("Failed to update username.")
            messagebox.showerror("Update Error", "Failed to update username!")

# UpdateEmailPage class
class UpdateEmailPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Build the page
        tk.Label(self, text="Update Email", font=("Arial", 16)).pack(pady=20)
        tk.Label(self, text="New Email").pack()
        self.new_email_entry = tk.Entry(self)
        self.new_email_entry.pack()
        tk.Button(self, text="Update", command=self.update_email).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ProfileManagementPage")).pack(pady=10)

    def update_email(self):
        new_email = self.new_email_entry.get().strip()
        if not new_email:
            messagebox.showerror("Update Error", "Email cannot be empty!")
            return
        success = self.controller.user_manager.update_email(new_email)
        if success:
            logging.info(f"Email updated to {new_email}.")
            messagebox.showinfo("Update Email", f"Email updated to {new_email} successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            logging.error("Email update failed: Email already in use or failed to update.")
            messagebox.showerror("Update Error", "Email already in use or failed to update!")

# ChangePasswordPage class
class ChangePasswordPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
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
        if not current_password or not new_password:
            messagebox.showerror("Change Password Error", "All fields are required!")
            return
        success = self.controller.user_manager.change_password(current_password, new_password)
        if success:
            logging.info("Password changed successfully.")
            messagebox.showinfo("Change Password", "Password changed successfully!")
            self.controller.show_frame("ProfileManagementPage")
        else:
            logging.error("Change password failed: Incorrect current password.")
            messagebox.showerror("Change Password Error", "Current password is incorrect!")

# SchedulePostPage class
class SchedulePostPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.media_file = None

        # Build the page
        tk.Label(self, text="Schedule Post", font=("Arial", 16)).pack(pady=10)

        # Platform selection
        tk.Label(self, text="Select Platform").pack()
        self.platform_var = tk.StringVar()
        self.platform_var.set('Select Platform')
        platforms = ['Facebook', 'Instagram']
        self.platform_menu = ttk.Combobox(self, textvariable=self.platform_var, values=platforms, state='readonly')
        self.platform_menu.pack()

        # Time zone selection
        tk.Label(self, text="Select Time Zone").pack()
        self.timezone_var = tk.StringVar()
        timezones = pytz.all_timezones
        self.timezone_menu = ttk.Combobox(self, textvariable=self.timezone_var, values=timezones, state='readonly')
        self.timezone_menu.pack()
        self.timezone_menu.set('UTC')  # Default timezone

        # Date selection using tkcalendar
        tk.Label(self, text="Select Date").pack()
        self.calendar = Calendar(self, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendar.pack(pady=5)

        # Time selection
        time_frame = tk.Frame(self)
        time_frame.pack(pady=5)
        tk.Label(time_frame, text="Select Time (24-hour format)").pack(side=tk.LEFT)
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()
        hours = [f"{i:02}" for i in range(24)]
        minutes = [f"{i:02}" for i in range(60)]
        self.hour_menu = ttk.Combobox(time_frame, textvariable=self.hour_var, values=hours, width=3, state='readonly')
        self.hour_menu.pack(side=tk.LEFT, padx=5)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute_menu = ttk.Combobox(time_frame, textvariable=self.minute_var, values=minutes, width=3, state='readonly')
        self.minute_menu.pack(side=tk.LEFT, padx=5)
        self.hour_menu.set('00')
        self.minute_menu.set('00')

        # Recurrence selection
        tk.Label(self, text="Recurrence (Optional)").pack()
        self.recurrence_var = tk.StringVar()
        self.recurrence_var.set('None')
        recurrences = ['None', 'Daily', 'Weekly', 'Monthly']
        self.recurrence_menu = ttk.Combobox(self, textvariable=self.recurrence_var, values=recurrences, state='readonly')
        self.recurrence_menu.pack()

        # Content text area
        tk.Label(self, text="Content").pack()
        self.content_text = tk.Text(self, height=5, width=60)
        self.content_text.pack()

        # Media options
        tk.Label(self, text="Media Files (Optional)").pack()
        tk.Button(self, text="Select Media File", command=self.select_media_file).pack(pady=5)
        self.media_label = tk.Label(self, text="No media file selected")
        self.media_label.pack()

        # Buttons
        tk.Button(self, text="Schedule Post", command=self.schedule_post).pack(pady=10)
        tk.Button(self, text="Post Now", command=self.post_now).pack(pady=5)
        tk.Button(self, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(pady=5)

    def select_media_file(self):
        file_types = [("All Files", "*.*")]
        platform = self.platform_var.get()
        if platform == 'Instagram':
            # For Instagram, media is required
            file_types = [("Image Files", "*.png;*.jpg;*.jpeg"), ("Video Files", "*.mp4;*.avi;*.mov")]
        elif platform == 'Facebook':
            # For Facebook, media is optional
            file_types = [("Image and Video Files", "*.png;*.jpg;*.jpeg;*.gif;*.mp4;*.avi;*.mov")]

        file_path = filedialog.askopenfilename(title="Select Media File", filetypes=file_types)
        if file_path:
            self.media_file = file_path
            self.media_label.config(text=f"Selected: {os.path.basename(file_path)}")

    def load_from_draft(self, draft):
        # Pre-fill the scheduling form with draft data
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert(tk.END, draft.content)
        if draft.media_files:
            self.media_file = draft.media_files[0]
            self.media_label.config(text=f"Selected: {os.path.basename(self.media_file)}")
        else:
            self.media_file = None
            self.media_label.config(text="No media file selected")
        # Assume platforms are the same
        if 'Facebook' in draft.platforms and 'Instagram' in draft.platforms:
            self.platform_var.set('Facebook')  # Default selection
        elif 'Facebook' in draft.platforms:
            self.platform_var.set('Facebook')
        elif 'Instagram' in draft.platforms:
            self.platform_var.set('Instagram')
        else:
            self.platform_var.set('Select Platform')
        self.timezone_menu.set('UTC')
        self.recurrence_var.set('None')
        self.calendar.selection_clear()
        self.hour_menu.set('00')
        self.minute_menu.set('00')

    def load_from_scheduled_post(self, scheduled_post):
        # Pre-fill the scheduling form with scheduled post data
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert(tk.END, scheduled_post.post.content)
        if scheduled_post.post.media_files:
            self.media_file = scheduled_post.post.media_files[0]
            self.media_label.config(text=f"Selected: {os.path.basename(self.media_file)}")
        else:
            self.media_file = None
            self.media_label.config(text="No media file selected")
        self.platform_var.set(scheduled_post.platform)
        self.timezone_var.set(scheduled_post.timezone)
        self.calendar.set_date(scheduled_post.scheduled_time.strftime('%Y-%m-%d'))
        self.hour_menu.set(scheduled_post.scheduled_time.strftime('%H'))
        self.minute_menu.set(scheduled_post.scheduled_time.strftime('%M'))
        self.recurrence_var.set(scheduled_post.recurrence if scheduled_post.recurrence else 'None')

    def schedule_post(self):
        platform = self.platform_var.get()
        timezone = self.timezone_var.get()
        selected_date = self.calendar.get_date()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        recurrence = self.recurrence_var.get()
        content = self.content_text.get("1.0", tk.END).strip()

        if platform not in ['Facebook', 'Instagram']:
            messagebox.showerror("Schedule Post Error", "Please select a platform.")
            return

        try:
            scheduled_time_naive = datetime.strptime(f"{selected_date} {hour}:{minute}", '%Y-%m-%d %H:%M')
            timezone_obj = pytz.timezone(timezone)
            scheduled_time = timezone_obj.localize(scheduled_time_naive)
            if scheduled_time <= datetime.now(timezone_obj):
                messagebox.showerror("Schedule Post Error", "Scheduled time must be in the future.")
                return
        except ValueError:
            messagebox.showerror("Schedule Post Error", "Invalid date and time format.")
            return

        media_files = [self.media_file] if self.media_file else []

        if platform == 'Instagram':
            if not media_files:
                messagebox.showerror("Schedule Post Error", "Instagram posts require a media file.")
                return
        elif platform == 'Facebook':
            if not content and not media_files:
                messagebox.showerror("Schedule Post Error", "Facebook posts require content or a media file.")
                return

        post = Post(content, media_files, [platform])
        scheduled_post = ScheduledPost(post, platform, scheduled_time, timezone, recurrence if recurrence != 'None' else None)
        self.controller.scheduled_posts.append(scheduled_post)
        self.controller.notification_log.add_notification(f"Post scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} on {platform}.")
        logging.info(f"Post scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} on {platform}.")
        messagebox.showinfo("Schedule Post", "Post scheduled successfully!")
        # Clear the form
        self.platform_var.set('Select Platform')
        self.timezone_var.set('UTC')
        self.calendar.selection_clear()
        self.hour_menu.set('00')
        self.minute_menu.set('00')
        self.recurrence_var.set('None')
        self.content_text.delete("1.0", tk.END)
        self.media_file = None
        self.media_label.config(text="No media file selected")

    def post_now(self):
        # Post immediately based on the form data
        platform = self.platform_var.get()
        timezone = self.timezone_var.get()
        selected_date = self.calendar.get_date()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        recurrence = self.recurrence_var.get()
        content = self.content_text.get("1.0", tk.END).strip()

        if platform not in ['Facebook', 'Instagram']:
            messagebox.showerror("Post Now Error", "Please select a platform.")
            return

        try:
            scheduled_time_naive = datetime.strptime(f"{selected_date} {hour}:{minute}", '%Y-%m-%d %H:%M')
            timezone_obj = pytz.timezone(timezone)
            scheduled_time = timezone_obj.localize(scheduled_time_naive)
            if scheduled_time <= datetime.now(timezone_obj):
                messagebox.showerror("Post Now Error", "Scheduled time must be in the future.")
                return
        except ValueError:
            messagebox.showerror("Post Now Error", "Invalid date and time format.")
            return

        media_files = [self.media_file] if self.media_file else []

        if platform == 'Instagram':
            if not media_files:
                messagebox.showerror("Post Now Error", "Instagram posts require a media file.")
                return
        elif platform == 'Facebook':
            if not content and not media_files:
                messagebox.showerror("Post Now Error", "Facebook posts require content or a media file.")
                return

        post = Post(content, media_files, [platform])
        post_to_social_media(self.controller, post, platform)
        self.controller.notification_log.add_notification(f"Post posted immediately on {platform}.")
        logging.info(f"Post posted immediately on {platform}.")
        messagebox.showinfo("Post Now", "Post published successfully!")
        # Clear the form
        self.platform_var.set('Select Platform')
        self.timezone_var.set('UTC')
        self.calendar.selection_clear()
        self.hour_menu.set('00')
        self.minute_menu.set('00')
        self.recurrence_var.set('None')
        self.content_text.delete("1.0", tk.END)
        self.media_file = None
        self.media_label.config(text="No media file selected")

# ViewScheduledPostsPage class
class ViewScheduledPostsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Build the page
        tk.Label(self, text="Scheduled Posts", font=("Arial", 16)).pack(pady=10)

        # Treeview to display scheduled posts
        columns = ('Platform', 'Content', 'Scheduled Time', 'Time Zone', 'Recurrence')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind('<Double-1>', self.edit_scheduled_post)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Edit Post", command=self.edit_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Post", command=self.delete_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Copy Post", command=self.copy_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(side=tk.LEFT, padx=5)

    def update_scheduled_posts_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, scheduled_post in enumerate(self.controller.scheduled_posts):
            time_str = scheduled_post.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
            self.tree.insert('', tk.END, values=(
                scheduled_post.platform,
                scheduled_post.post.content[:30] + '...',
                time_str,
                scheduled_post.timezone,
                scheduled_post.recurrence if scheduled_post.recurrence else 'None'
            ))

    def edit_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            scheduled_post = self.controller.scheduled_posts[index]
            # Pre-fill the scheduling form with scheduled post data
            schedule_page = self.controller.frames['SchedulePostPage']
            schedule_page.load_from_scheduled_post(scheduled_post)
            self.controller.show_frame('SchedulePostPage')
            # Remove the old scheduled post
            del self.controller.scheduled_posts[index]
            self.update_scheduled_posts_list()
        else:
            messagebox.showerror("Edit Post Error", "Please select a post to edit.")

    def delete_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            confirm = messagebox.askyesno("Delete Scheduled Post", "Are you sure you want to delete this scheduled post?")
            if confirm:
                del self.controller.scheduled_posts[index]
                self.controller.save_users()
                self.update_scheduled_posts_list()
                logging.info(f"Scheduled post {index+1} deleted successfully.")
                messagebox.showinfo("Delete Post", "Scheduled post deleted successfully!")
        else:
            messagebox.showerror("Delete Post Error", "Please select a post to delete.")

    def copy_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            scheduled_post = self.controller.scheduled_posts[index]
            new_post = Post(scheduled_post.post.content, scheduled_post.post.media_files.copy(), scheduled_post.post.platforms.copy())
            new_scheduled_post = ScheduledPost(new_post, scheduled_post.platform, scheduled_post.scheduled_time, scheduled_post.timezone, scheduled_post.recurrence)
            self.controller.scheduled_posts.append(new_scheduled_post)
            self.update_scheduled_posts_list()
            logging.info(f"Scheduled post {index+1} copied successfully.")
            messagebox.showinfo("Copy Post", "Scheduled post copied successfully!")
        else:
            messagebox.showerror("Copy Post Error", "Please select a post to copy.")

    def edit_scheduled_post(self, event):
        self.edit_post()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_scheduled_posts_list()

# NotificationLogPage class
class NotificationLogPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Build the page
        tk.Label(self, text="Notification Log", font=("Arial", 16)).pack(pady=10)

        # Listbox to display notifications
        self.listbox = tk.Listbox(self, width=100)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar for the listbox
        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(side=tk.LEFT, padx=5)

    def update_log(self):
        self.listbox.delete(0, tk.END)
        for notification in self.controller.notification_log.notifications:
            self.listbox.insert(tk.END, notification)

    def clear_log(self):
        self.controller.notification_log.clear_log()
        self.update_log()
        messagebox.showinfo("Clear Log", "Notification log cleared successfully.")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_log()

# ViewScheduledPostsPage class
class ViewScheduledPostsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Build the page
        tk.Label(self, text="Scheduled Posts", font=("Arial", 16)).pack(pady=10)

        # Treeview to display scheduled posts
        columns = ('Platform', 'Content', 'Scheduled Time', 'Time Zone', 'Recurrence')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind('<Double-1>', self.edit_scheduled_post)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Edit Post", command=self.edit_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Post", command=self.delete_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Copy Post", command=self.copy_post).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: controller.show_frame("ApplicationPage")).pack(side=tk.LEFT, padx=5)

    def update_scheduled_posts_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, scheduled_post in enumerate(self.controller.scheduled_posts):
            time_str = scheduled_post.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
            self.tree.insert('', tk.END, values=(
                scheduled_post.platform,
                scheduled_post.post.content[:30] + '...',
                time_str,
                scheduled_post.timezone,
                scheduled_post.recurrence if scheduled_post.recurrence else 'None'
            ))

    def edit_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            scheduled_post = self.controller.scheduled_posts[index]
            # Pre-fill the scheduling form with scheduled post data
            schedule_page = self.controller.frames['SchedulePostPage']
            schedule_page.load_from_scheduled_post(scheduled_post)
            self.controller.show_frame('SchedulePostPage')
            # Remove the old scheduled post
            del self.controller.scheduled_posts[index]
            self.update_scheduled_posts_list()
        else:
            messagebox.showerror("Edit Post Error", "Please select a post to edit.")

    def delete_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            confirm = messagebox.askyesno("Delete Scheduled Post", "Are you sure you want to delete this scheduled post?")
            if confirm:
                del self.controller.scheduled_posts[index]
                self.controller.save_users()
                self.update_scheduled_posts_list()
                logging.info(f"Scheduled post {index+1} deleted successfully.")
                messagebox.showinfo("Delete Post", "Scheduled post deleted successfully!")
        else:
            messagebox.showerror("Delete Post Error", "Please select a post to delete.")

    def copy_post(self):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected)
            scheduled_post = self.controller.scheduled_posts[index]
            new_post = Post(scheduled_post.post.content, scheduled_post.post.media_files.copy(), scheduled_post.post.platforms.copy())
            new_scheduled_post = ScheduledPost(new_post, scheduled_post.platform, scheduled_post.scheduled_time, scheduled_post.timezone, scheduled_post.recurrence)
            self.controller.scheduled_posts.append(new_scheduled_post)
            self.update_scheduled_posts_list()
            logging.info(f"Scheduled post {index+1} copied successfully.")
            messagebox.showinfo("Copy Post", "Scheduled post copied successfully!")
        else:
            messagebox.showerror("Copy Post Error", "Please select a post to copy.")

    def edit_scheduled_post(self, event):
        self.edit_post()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_scheduled_posts_list()

# -------------------- Running the Application -------------------- #

if __name__ == "__main__":
    # **IMPORTANT:** Ensure that your Instagram credentials are securely stored as environment variables.
    # Do NOT hard-code your credentials in the code.
    # Use a .env file or set environment variables in your operating system.

    # Initialize and run the application
    app = App()
    app.mainloop()
