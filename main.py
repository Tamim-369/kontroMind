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
            text="Start Monitoring (10 min)", 
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
        
        # Create a frame for the image gallery with scrolling
        self.gallery_frame = customtkinter.CTkScrollableFrame(self)
        self.gallery_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.gallery_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = customtkinter.CTkLabel(
            self, 
            text="Status: Idle",
            font=("Helvetica", 12)
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

    def upload_image(self):
        # Use the system's native file dialog (this is default behavior in tkinter)
        file_paths = filedialog.askopenfilenames(
            parent=self,  # Set parent to ensure it's a modal dialog
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
            # Fixed: Get the appearance mode and theme colors properly
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
                
            self.monitoring = True
            self.start_button.configure(text="Stop Monitoring", fg_color="red")
            self.status_label.configure(text="Status: Monitoring active...")
            
            # Start monitoring in a separate thread
            self.monitor_thread = threading.Thread(target=self.monitor_screen)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.start_button.configure(text="Start Monitoring (10 min)", fg_color="green")
            self.status_label.configure(text="Status: Monitoring stopped")
    
    def monitor_screen(self):
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        
        start_time = time.time()
        duration = 600  # 10 minutes in seconds
        
        while self.monitoring and (time.time() - start_time) < duration:
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
            self.after(0, lambda: self.status_label.configure(text="Status: Monitoring completed (10 min)"))
            self.after(0, lambda: self.start_button.configure(text="Start Monitoring (10 min)", fg_color="green"))
            self.monitoring = False

if __name__ == "__main__":
    app = App()
    app.mainloop()