import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os



def select_image():
    
    file_path = filedialog.askopenfilename(
        initialdir="E:/DCIM/Camera", 
        title="Select an Image",
        filetypes=(("jpeg files", "*.jpg"), ("png files", "*.png"), ("all files", "*.*"))
    )
    
    
    if file_path:
        try:
            pil_image = Image.open(file_path)
            resized_image = pil_image.resize((400, 550), Image.LANCZOS)
            
            tk_image = ImageTk.PhotoImage(resized_image)
            label.config(image=tk_image)
            label.image = tk_image
            save_resized_image(resized_image) 
        except Exception as e:
            print(f"Error loading image: {e}")
            
def save_resized_image(image):
    save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=(("jpeg files",  "*.jpg"), ("png files", "*.png"), ("all files", "*.*")))
    if save_path:
        try:
            image.save(save_path)
            print(f"Image saved to {save_path}")
        except Exception as e:
            print(f"Error saving image: {e}")


root = tk.Tk()
root.title("Select Image")
root.geometry("700x1280")
root.configure(bg="orange")

def exit_os():
    root.destroy()
    

button = tk.Button(root, text="Load Image", command=select_image)
button.pack()

exit_button = tk.Button(root, text="Exit", command=exit_os)
button.pack()


label = tk.Label(root)
label.pack()


root.mainloop()