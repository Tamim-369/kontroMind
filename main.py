import customtkinter
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import threading
import time
import pyttsx3
import pyautogui
import numpy as np
import cv2

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
        
        # Duration settings frame
        self.duration_frame = customtkinter.CTkFrame(self)
        self.duration_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.duration_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.duration_frame.grid_remove()  # Initially hidden
        
        # Duration input
        self.duration_value = customtkinter.CTkEntry(
            self.duration_frame,
            width=80
        )
        self.duration_value.insert(0, "10")  # Default value
        self.duration_value.grid(row=0, column=0, padx=10, pady=10)
        
        # Duration unit selection
        self.duration_unit = customtkinter.CTkSegmentedButton(
            self.duration_frame,
            values=["Minutes", "Hours", "Days"],
            command=self.update_duration_label
        )
        self.duration_unit.grid(row=0, column=1, padx=10, pady=10)
        self.duration_unit.set("Minutes")  # Default selection
        
        # Apply button
        self.apply_button = customtkinter.CTkButton(
            self.duration_frame,
            text="Apply",
            command=self.apply_duration,
            fg_color="green",
            width=80
        )
        self.apply_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Close button
        self.close_duration_button = customtkinter.CTkButton(
            self.duration_frame,
            text="Close",
            command=self.close_duration_settings,
            fg_color="gray",
            width=80
        )
        self.close_duration_button.grid(row=0, column=3, padx=10, pady=10)
        
        # Toggle duration settings button
        self.duration_toggle = customtkinter.CTkButton(
            self.buttons_frame,
            text="⏱️ Duration Settings",
            command=self.toggle_duration_settings,
            width=30
        )
        self.duration_toggle.grid(row=1, column=1, padx=10, pady=(0, 10))
        
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
        self.duration_display.pack(pady=(0, 50))
        
        # Status label
        self.status_label = customtkinter.CTkLabel(
            self, 
            text="Status: Idle",
            font=("Helvetica", 12)
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Duration settings flag
        self.duration_settings_visible = False
        
        # Default duration in seconds (10 minutes)
        self.monitoring_duration = 600
        
        # Initialize the button text
        self.update_duration()

    def toggle_duration_settings(self):
        if not self.duration_settings_visible:
            self.duration_frame.grid()
            self.duration_settings_visible = True
        else:
            self.close_duration_settings()
    
    def close_duration_settings(self):
        self.duration_frame.grid_remove()
        self.duration_settings_visible = False
    
    def apply_duration(self):
        self.update_duration()
        self.close_duration_settings()
        self.status_label.configure(text=f"Status: Duration set to {self.get_duration_display()}")
    
    def update_duration_label(self, value=None):
        self.update_duration()
    
    def get_duration_display(self):
        try:
            duration_value = float(self.duration_value.get())
            duration_unit = self.duration_unit.get()
            
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
            duration_value = float(self.duration_value.get())
            if duration_value <= 0:
                duration_value = 10  # Default to 10 if invalid
                self.duration_value.delete(0, tk.END)
                self.duration_value.insert(0, "10")
                
            duration_unit = self.duration_unit.get()
            
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
            self.duration_value.delete(0, tk.END)
            self.duration_value.insert(0, "10")
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
            
            # Disable buttons during monitoring
            self.upload_button.configure(state="disabled")
            self.clear_button.configure(state="disabled")
            self.duration_toggle.configure(state="disabled")
            
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
            self.duration_toggle.configure(state="normal")
    
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
    
    def monitor_screen(self):
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        
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
                    # Image found, speak the message
                    message = "What the fact are you doing"
                    engine.say(message)
                    engine.runAndWait()
                    
                    # Update status
                    self.after(0, lambda: self.status_label.configure(text="Status: Image detected!"))
                    
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