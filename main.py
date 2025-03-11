import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x200")
        self.title("CustomTkinter Example")
        self.label  = customtkinter.CTkLabel(self, text="Enter details about the person you want to become.", text_color="gray").pack()
        # Creating a Textbox (Multiline Input)
        self.input = customtkinter.CTkTextbox(self, height=100, width=300)
        self.input.pack(padx=20, pady=10)


        # Button
        self.button = customtkinter.CTkButton(self, text="Start", command=self.button_callback)
        self.button.pack(padx=20, pady=10)

    def button_callback(self):
        text_content = self.input.get("1.0", "end").strip()  
        print("Button clicked! Input value:", text_content)

app = App()
app.mainloop()
