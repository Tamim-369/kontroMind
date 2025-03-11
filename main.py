import customtkinter
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
import os
import threading
import time
import pyttsx3
import pyautogui
import numpy as np
import cv2
import json
import keyboard

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Image Monitoring App")
        
        # Store uploaded images
        self.images = []
        self.image_paths = []
        self.monitoring = False
        self.monitor_thread = None
        
        # Default settings
        self.config_file = "monitor_config.json"
        self.default_settings = {
            "duration": 10,
            "duration_unit": "Minutes",
            "keyboard_shortcut": "alt+f4",
            "custom_text": "What the fact are you doing",
            "action_type": "speak"  # Options: "speak", "keyboard", "both"
        }
        self.settings = self.load_settings()
        
        # Configure the grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Header section
        self.label = customtkinter.CTkLabel(
            self, 
            text="Upload images you want to monitor on your screen",
            font=("Helvetica", 16)
        )
        self.label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")
        
        # Buttons frame
        self.buttons_frame = customtkinter.CTkFrame(self)
        self.buttons_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Upload button
        self.upload_button = customtkinter.CTkButton(
            self.buttons_frame, 
            text="Upload Image", 
            command=self.upload_image
        )
        self.upload_button.grid(row=0, column=0, padx=10, pady=10)
        
        # Start monitoring button
        self.start_button = customtkinter.CTkButton(
            self.buttons_frame, 
            text="Start Monitoring", 
            command=self.toggle_monitoring,
            fg_color="green"
        )
        self.start_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Clear images button
        self.clear_button = customtkinter.CTkButton(
            self.buttons_frame, 
            text="Clear All Images", 
            command=self.clear_images,
            fg_color="red"
        )
        self.clear_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Settings button
        self.settings_toggle = customtkinter.CTkButton(
            self.buttons_frame,
            text="⚙️ Settings",
            command=self.toggle_settings,
            width=30
        )
        self.settings_toggle.grid(row=1, column=1, padx=10, pady=(0, 10))
        
        # Settings frame (initially hidden)
        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.settings_frame.grid_remove()  # Initially hidden
        
        # Create notebook/tabs for settings
        self.settings_tabs = customtkinter.CTkTabview(self.settings_frame)
        self.settings_tabs.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Add tabs
        self.settings_tabs.add("Duration")
        self.settings_tabs.add("Actions")
        
        # Duration Settings Tab
        duration_tab = self.settings_tabs.tab("Duration")
        duration_tab.grid_columnconfigure((0, 1), weight=1)
        
        # Duration input
        customtkinter.CTkLabel(duration_tab, text="Duration:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="e")
        
        self.duration_value = customtkinter.CTkEntry(
            duration_tab,
            width=80
        )
        self.duration_value.insert(0, str(self.settings["duration"]))
        self.duration_value.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
        
        # Duration unit selection
        customtkinter.CTkLabel(duration_tab, text="Unit:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.duration_unit = customtkinter.CTkSegmentedButton(
            duration_tab,
            values=["Minutes", "Hours", "Days"]
        )
        self.duration_unit.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.duration_unit.set(self.settings["duration_unit"])
        
        # Actions Settings Tab
        actions_tab = self.settings_tabs.tab("Actions")
        actions_tab.grid_columnconfigure((0, 1), weight=1)
        
        # Action type selection
        customtkinter.CTkLabel(actions_tab, text="When image detected:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w", columnspan=2)
        
        self.action_type = customtkinter.CTkSegmentedButton(
            actions_tab,
            values=["Speak Text", "Press Shortcut", "Both"]
        )
        self.action_type.grid(row=1, column=0, padx=10, pady=10, sticky="ew", columnspan=2)
        
        # Convert stored setting to display value
        action_map = {"speak": "Speak Text", "keyboard": "Press Shortcut", "both": "Both"}
        self.action_type.set(action_map.get(self.settings["action_type"], "Speak Text"))
        
        # Custom text option
        customtkinter.CTkLabel(actions_tab, text="Text to speak:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        self.custom_text = customtkinter.CTkEntry(
            actions_tab,
            width=200
        )
        self.custom_text.insert(0, self.settings["custom_text"])
        self.custom_text.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        # Keyboard shortcut option
        customtkinter.CTkLabel(actions_tab, text="Keyboard shortcut:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        
        self.shortcut_frame = customtkinter.CTkFrame(actions_tab)
        self.shortcut_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        self.shortcut_label = customtkinter.CTkLabel(
            self.shortcut_frame,
            text=self.settings["keyboard_shortcut"]
        )
        self.shortcut_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.shortcut_button = customtkinter.CTkButton(
            self.shortcut_frame,
            text="Change",
            command=self.change_shortcut,
            width=80
        )
        self.shortcut_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Test buttons
        self.test_speak_button = customtkinter.CTkButton(
            actions_tab,
            text="Test Speech",
            command=self.test_speech,
            width=100
        )
        self.test_speak_button.grid(row=4, column=0, padx=10, pady=20)
        
        self.test_shortcut_button = customtkinter.CTkButton(
            actions_tab,
            text="Test Shortcut",
            command=self.test_shortcut,
            width=100
        )
        self.test_shortcut_button.grid(row=4, column=1, padx=10, pady=20)
        
        # Apply and close buttons for settings
        self.settings_buttons_frame = customtkinter.CTkFrame(self.settings_frame)
        self.settings_buttons_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.apply_settings_button = customtkinter.CTkButton(
            self.settings_buttons_frame,
            text="Save Settings",
            command=self.save_settings,
            fg_color="green",
            width=120
        )
        self.apply_settings_button.pack(side="left", padx=10, pady=10)
        
        self.close_settings_button = customtkinter.CTkButton(
            self.settings_buttons_frame,
            text="Close",
            command=self.close_settings,
            fg_color="gray",
            width=120
        )
        self.close_settings_button.pack(side="right", padx=10, pady=10)
        
        # Create a frame for the image gallery with scrolling
        self.gallery_frame = customtkinter.CTkScrollableFrame(self)
        self.gallery_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.gallery_frame.grid_columnconfigure(0, weight=1)
        
        # Create a monitoring message frame (initially hidden)
        self.monitoring_frame = customtkinter.CTkFrame(self)
        self.monitoring_message = customtkinter.CTkLabel(
            self.monitoring_frame,
            text="Monitoring in progress...\nApplication is watching for target images",
            font=("Helvetica", 16),
            text_color="white",
            justify="center"
        )
        self.monitoring_message.pack(pady=50)
        
        # Duration display label in monitoring frame
        self.duration_display = customtkinter.CTkLabel(
            self.monitoring_frame,
            text="Time remaining: 10:00",
            font=("Helvetica", 14),
            text_color="white"
        )
        self.duration_display.pack(pady=(0, 20))
        
        # Active actions display in monitoring frame
        self.actions_display = customtkinter.CTkLabel(
            self.monitoring_frame,
            text="",
            font=("Helvetica", 12),
            text_color="white"
        )
        self.actions_display.pack(pady=(0, 50))
        
        # Status label
        self.status_label = customtkinter.CTkLabel(
            self, 
            text="Status: Idle",
            font=("Helvetica", 12)
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Settings flag
        self.settings_visible = False
        
        # Update the button text
        self.update_duration()
        
        # Update actions display
        self.update_actions_display()

    def load_settings(self):
        """Load settings from file or use defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            # Get current values from UI
            self.settings["duration"] = float(self.duration_value.get())
            self.settings["duration_unit"] = self.duration_unit.get()
            self.settings["custom_text"] = self.custom_text.get()
            self.settings["keyboard_shortcut"] = self.shortcut_label.cget("text")
            
            # Convert action type to storage format
            action_map = {"Speak Text": "speak", "Press Shortcut": "keyboard", "Both": "both"}
            self.settings["action_type"] = action_map.get(self.action_type.get(), "speak")
            
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f)
                
            self.status_label.configure(text="Status: Settings saved")
            
            # Update UI elements
            self.update_duration()
            self.update_actions_display()
            
            # Close settings panel
            self.close_settings()
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.status_label.configure(text=f"Status: Error saving settings")
    
    def update_actions_display(self):
        """Update the actions display in the monitoring frame"""
        action_type = self.settings["action_type"]
        text = "Actions when image detected: "
        
        if action_type == "speak" or action_type == "both":
            text += f"Speak \"{self.settings['custom_text']}\""
            
        if action_type == "keyboard" or action_type == "both":
            if action_type == "both":
                text += " and "
            text += f"Press \"{self.settings['keyboard_shortcut']}\""
            
        self.actions_display.configure(text=text)
    
    def change_shortcut(self):
        """Open dialog to change keyboard shortcut"""
        self.shortcut_label.configure(text="Press key combination...")
        self.shortcut_button.configure(state="disabled")
        
        # Create a simple toplevel window to capture keypress
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Set Keyboard Shortcut")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        label = customtkinter.CTkLabel(
            dialog,
            text="Press the keyboard shortcut you want to use.\nESC to cancel.",
            font=("Helvetica", 14),
            justify="center"
        )
        label.pack(pady=20)
        
        result_label = customtkinter.CTkLabel(
            dialog,
            text="Waiting for input...",
            font=("Helvetica", 12)
        )
        result_label.pack(pady=10)
        
        # Variable to store the shortcut
        shortcut = []
        
        def on_key_event(e):
            key = e.name
            
            if key == "escape":
                dialog.destroy()
                self.shortcut_label.configure(text=self.settings["keyboard_shortcut"])
                self.shortcut_button.configure(state="normal")
                return
            
            # Clear if a new key is pressed
            if key not in ["ctrl", "alt", "shift"]:
                shortcut.clear()
            
            # Add modifier keys
            if e.event_type == "down":
                if key not in shortcut:
                    shortcut.append(key)
                
                # Display current combination
                shortcut_text = "+".join(shortcut)
                result_label.configure(text=shortcut_text)
                
                # If a non-modifier key is pressed, we're done
                if key not in ["ctrl", "alt", "shift"] and len(shortcut) > 0:
                    self.shortcut_label.configure(text=shortcut_text)
                    self.shortcut_button.configure(state="normal")
                    dialog.after(500, dialog.destroy)
        
        # Hook keyboard events
        keyboard.hook(on_key_event)
        
        # Unhook when dialog is closed
        def on_close():
            keyboard.unhook(on_key_event)
            dialog.destroy()
            self.shortcut_button.configure(state="normal")
        
        dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    def test_speech(self):
        """Test the speech function with current text"""
        try:
            engine = pyttsx3.init()
            engine.say(self.custom_text.get())
            engine.runAndWait()
        except Exception as e:
            print(f"Error testing speech: {e}")
            self.status_label.configure(text="Status: Error testing speech")
    
    def test_shortcut(self):
        """Test the keyboard shortcut (simulated message)"""
        self.status_label.configure(text=f"Status: Simulated pressing {self.shortcut_label.cget('text')}")
    
    def toggle_settings(self):
        if not self.settings_visible:
            self.settings_frame.grid()
            self.settings_visible = True
        else:
            self.close_settings()
    
    def close_settings(self):
        self.settings_frame.grid_remove()
        self.settings_visible = False
    
    def get_duration_display(self):
        try:
            duration_value = float(self.settings["duration"])
            duration_unit = self.settings["duration_unit"]
            
            if duration_unit == "Minutes":
                display_value = f"{int(duration_value) if duration_value.is_integer() else duration_value} min"
            elif duration_unit == "Hours":
                display_value = f"{int(duration_value) if duration_value.is_integer() else duration_value} hr"
            elif duration_unit == "Days":
                display_value = f"{int(duration_value) if duration_value.is_integer() else duration_value} day{'s' if duration_value > 1 else ''}"
                
            return display_value
        except:
            return "10 min"
    
    def update_duration(self):
        try:
            duration_value = float(self.settings["duration"])
            if duration_value <= 0:
                duration_value = 10  # Default to 10 if invalid
                self.settings["duration"] = 10
                
            duration_unit = self.settings["duration_unit"]
            
            # Convert to seconds
            if duration_unit == "Minutes":
                self.monitoring_duration = duration_value * 60
            elif duration_unit == "Hours":
                self.monitoring_duration = duration_value * 60 * 60
            elif duration_unit == "Days":
                self.monitoring_duration = duration_value * 24 * 60 * 60
            
            # Update start button text
            display_value = self.get_duration_display()
            self.start_button.configure(text=f"Start Monitoring ({display_value})")
            
        except ValueError:
            self.settings["duration"] = 10
            self.monitoring_duration = 600  # Default to 10 minutes

    def upload_image(self):
        # Only allow uploading when not monitoring
        if self.monitoring:
            return
            
        file_paths = filedialog.askopenfilenames(
            parent=self,
            title='Select images to upload',
            filetypes=(
                ('Image files', '*.jpg *.jpeg *.png *.bmp *.gif'),
                ('All files', '*.*')
            )
        )
        
        for file_path in file_paths:
            if file_path and file_path not in self.image_paths:
                self.image_paths.append(file_path)
                self.add_image_to_gallery(file_path)
                
        self.status_label.configure(text=f"Status: {len(self.images)} images loaded")

    def add_image_to_gallery(self, file_path):
        try:
            # Load and resize the image for display
            img = Image.open(file_path)
            img.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(img)
            
            # Create frame for image and label
            item_frame = customtkinter.CTkFrame(self.gallery_frame)
            item_frame.grid(row=len(self.images), column=0, padx=10, pady=10, sticky="ew")
            
            # Display image
            appearance_mode = customtkinter.get_appearance_mode().lower()
            if appearance_mode == "dark":
                bg_color = "#2b2b2b"  # Dark mode background
            else:
                bg_color = "#dbdbdb"  # Light mode background
                
            image_label = tk.Label(item_frame, image=photo, bg=bg_color)
            image_label.image = photo  # Keep a reference
            image_label.grid(row=0, column=0, padx=10, pady=10)
            
            # Display filename
            filename = os.path.basename(file_path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            text_label = customtkinter.CTkLabel(item_frame, text=filename)
            text_label.grid(row=1, column=0, padx=10, pady=(0, 10))
            
            # Store the image for monitoring
            original_img = cv2.imread(file_path)
            if original_img is not None:
                self.images.append(original_img)
            else:
                print(f"Warning: Could not load image {file_path} for monitoring")
                
        except Exception as e:
            print(f"Error adding image: {e}")
    
    def clear_images(self):
        # Only allow clearing when not monitoring
        if self.monitoring:
            return
            
        # Clear all images
        self.images = []
        self.image_paths = []
        
        # Remove all widgets from gallery
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()
            
        self.status_label.configure(text="Status: All images cleared")
    
    def toggle_monitoring(self):
        if not self.monitoring:
            if not self.images:
                self.status_label.configure(text="Status: No images to monitor")
                return
            
            # Update duration from settings
            self.update_duration()
            
            self.monitoring = True
            self.start_button.configure(text="Stop Monitoring", fg_color="red")
            self.status_label.configure(text="Status: Monitoring active...")
            
            # Hide the gallery and show monitoring message
            self.gallery_frame.grid_remove()
            self.monitoring_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
            
            # Update actions display
            self.update_actions_display()
            
            # Disable buttons during monitoring
            self.upload_button.configure(state="disabled")
            self.clear_button.configure(state="disabled")
            self.settings_toggle.configure(state="disabled")
            
            # Start monitoring in a separate thread
            self.monitor_thread = threading.Thread(target=self.monitor_screen)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.update_duration()  # Update the button text with current duration
            self.status_label.configure(text="Status: Monitoring stopped")
            
            # Show the gallery again and hide monitoring message
            self.monitoring_frame.grid_remove()
            self.gallery_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
            
            # Re-enable buttons
            self.upload_button.configure(state="normal")
            self.clear_button.configure(state="normal")
            self.settings_toggle.configure(state="normal")
    
    def format_time_remaining(self, seconds):
        """Format seconds into appropriate units for display"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {seconds % 60}s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"
    
    def perform_actions(self):
        """Perform configured actions when an image is detected"""
        action_type = self.settings["action_type"]
        detected = False
        
        try:
            # Speak text
            if action_type == "speak" or action_type == "both":
                engine = pyttsx3.init()
                engine.say(self.settings["custom_text"])
                engine.runAndWait()
                detected = True
                
            # Send keyboard shortcut
            if action_type == "keyboard" or action_type == "both":
                keyboard.press_and_release(self.settings["keyboard_shortcut"])
                detected = True
                
            # Update status
            if detected:
                self.after(0, lambda: self.status_label.configure(text="Status: Image detected! Actions performed"))
        except Exception as e:
            print(f"Error performing actions: {e}")
            self.after(0, lambda: self.status_label.configure(text="Status: Error performing actions"))
    
    def monitor_screen(self):
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < self.monitoring_duration:
            # Update time remaining display
            time_remaining = int(self.monitoring_duration - (time.time() - start_time))
            formatted_time = self.format_time_remaining(time_remaining)
            self.after(0, lambda t=formatted_time: self.duration_display.configure(
                text=f"Time remaining: {t}"))
            
            # Take a screenshot
            screenshot = pyautogui.screenshot()
            screenshot = np.array(screenshot)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
            
            # Check for each monitored image
            for img in self.images:
                result = cv2.matchTemplate(screenshot, img, cv2.TM_CCOEFF_NORMED)
                threshold = 0.7  # Adjust threshold as needed
                locations = np.where(result >= threshold)
                
                if len(locations[0]) > 0:
                    # Image found, perform actions
                    self.after(0, self.perform_actions)
                    
                    # Small delay to avoid repeated alerts
                    time.sleep(3)
                    break
            
            # Small delay between checks to reduce CPU usage
            time.sleep(0.5)
        
        # When monitoring ends
        if self.monitoring:  # If time is up but not manually stopped
            display_time = self.get_duration_display()
            self.after(0, lambda: self.status_label.configure(
                text=f"Status: Monitoring completed ({display_time})"))
            self.after(0, self.update_duration)  # Update button text
            self.after(0, lambda: self.toggle_monitoring())  # Call toggle to reset UI

if __name__ == "__main__":
    app = App()
    app.mainloop()