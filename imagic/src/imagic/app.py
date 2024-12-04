"""
Magic Image Processing Tool

History
When      | Who        | What
03/12/2024| TQ Ye      | First version
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter

import tkinter as tk
from tkinter import colorchooser

import tempfile
import asyncio
import os
import shutil

class ImageMagic(toga.App):
    def startup(self):
        """
        Construct and show the Toga application.
        """
        self.main_box = toga.Box(style=Pack(direction=COLUMN))
        self.setup_ui_components()
        self.setup_window()

    def setup_ui_components(self):
        """Setup all UI components"""
        self.create_title()
        self.create_upload_section()
        self.create_processing_section()
        self.create_image_display_section()
        
        # Add all components to main box
        self.main_box.add(self.title_label)
        self.main_box.add(self.upload_button)
        self.main_box.add(self.proc_option_box)
        self.main_box.add(self.params_box)
        self.main_box.add(self.process_button)
        self.main_box.add(self.image_box)

    def create_title(self):
        """Create the title section"""
        self.title_label = toga.Label('Image Magic', style=Pack(padding=10))

    def setup_window(self):
        """Setup the main window"""
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    def create_upload_section(self):
        """Create the upload button and related functionality"""
        self.upload_button = toga.Button(
            'Upload Image',
            on_press=self.handle_file_upload,
            style=Pack(padding=10)
        )

    def create_processing_section(self):
        """Create the processing options and button"""
        # Create processing options box
        self.proc_option_box = toga.Box(style=Pack(direction=ROW, padding=10))
        
        # Add dropdown label and list
        dropdown_label = toga.Label(
            'Choose Processing:',
            style=Pack(padding=(0, 10, 0, 0))
        )
        
        self.dropdown = toga.Selection(
            items=['Remove Background', 'Enhance Image'],
            on_select=self.handle_option_select,
            style=Pack(flex=1)
        )
        
        # Create parameters box
        self.params_box = toga.Box(style=Pack(direction=ROW, padding=10))
    
        self.proc_option_box.add(dropdown_label)
        self.proc_option_box.add(self.dropdown)
        
        # Create process button
        self.process_button = toga.Button(
            'Process Image',
            on_press=self.handle_processing,
            enabled=False,
            style=Pack(padding=10)
        )

    def create_image_display_section(self):
        """Create the image display section"""
        self.image_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Create a row for images
        image_row = toga.Box(style=Pack(direction=ROW))

        # Original image section
        original_section = toga.Box(style=Pack(direction=COLUMN, padding=10))
        original_label = toga.Label(
            'Original Image:',
            style=Pack(padding=(0, 0, 10, 0))
        )
        self.original_image_box = toga.Box(style=Pack(padding=10))
        original_section.add(original_label)
        original_section.add(self.original_image_box)
        
        # Processed image section
        processed_section = toga.Box(style=Pack(direction=COLUMN, padding=10))
        processed_label = toga.Label(
            'Processed Image:',
            style=Pack(padding=(0, 0, 10, 0))
        )
        self.processed_image_box = toga.Box(style=Pack(padding=10))
        processed_section.add(processed_label)
        processed_section.add(self.processed_image_box)
        
        # Add original and processed sections to the image row
        image_row.add(original_section)
        image_row.add(processed_section)
        
        # Add the image row to the main image box
        self.image_box.add(image_row)
        
        # Create download button (initially hidden)
        self.download_button = toga.Button(
            'Save Processed Image',
            on_press=self.handle_download,
            style=Pack(padding=10)
        )
        self.download_button.enabled = False
        
        # Add download button to image box
        self.image_box.add(self.download_button)

    async def handle_download(self, widget):
        """Handle the download of processed image"""
        try:
            # Get the processed image path
            if not hasattr(self, 'processed_image_path'):
                print('No processed image available')
                return
                
            # Open save file dialog
            save_path = await self.main_window.save_file_dialog(
                "Save processed image",
                suggested_filename="processed_image.png",
                file_types=['png']
            )
            
            if save_path:
                # Copy the processed image to the selected location
                shutil.copy2(self.processed_image_path, save_path)
                print(f'Image saved to: {save_path}')
                
        except Exception as e:
            print(f'Error saving image: {e}')
            import traceback
            traceback.print_exc()

    async def handle_file_upload(self, widget):
        """Handle file upload process"""
        try:
            file_path = await self.main_window.open_file_dialog(
                title="Select an image file",
                multiselect=False,
                file_types=['png', 'jpg', 'jpeg', 'gif']
            )
            if file_path:
                if self.is_valid_image(file_path):
                    self.display_image(file_path, self.original_image_box)
                    self.process_button.enabled = True
                    
                    # Clear processed image and disable download button
                    self.processed_image_box.clear()
                    self.download_button.enabled = False
                    
                    # Clean up the previous processed image if it exists
                    if hasattr(self, 'processed_image_path'):
                        try:
                            os.remove(self.processed_image_path)
                            delattr(self, 'processed_image_path')
                        except Exception as e:
                            print(f'Error cleaning up temporary file: {e}')
                else:
                    self.process_button.enabled = False
                    print('Invalid file type. Please upload an image file.')
        except Exception as e:
            print(f'Error uploading file: {e}')

    def is_valid_image(self, file_path):
        """Check if the file is a valid image"""
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        return any(str(file_path).lower().endswith(ext) for ext in allowed_extensions)

    def display_image(self, file_path, container):
        """
        Display an image in the specified container with max dimensions of 200x200
        while maintaining aspect ratio
        """
        container.clear()
        
        # Create the image and get its dimensions
        image = toga.Image(file_path)
        width = image.width
        height = image.height
        
        # Calculate new dimensions maintaining aspect ratio
        max_size = 300
        if width > height:
            new_width = max_size
            new_height = int((height / width) * max_size)
        else:
            new_height = max_size
            new_width = int((width / height) * max_size)
            
        # Create and add the image view with the new size
        image_view = toga.ImageView(image)
        image_view.style.update(
            width=new_width,
            height=new_height,
            padding=5
        )
        container.add(image_view)

    def open_color_picker(self, widget):
        """Open a color picker dialog and store the selected color"""
        # Initialize tkinter root
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        # Open color picker dialog
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code[0]:
            r, g, b = color_code[0]
            self.selected_color = (r, g, b, 255)  # Add full opacity for alpha
            print(f'Selected color: {self.selected_color}')

    def handle_option_select(self, widget):
        """Handle processing option selection"""
        print(f'Selected option: {widget.value}')

        # Clear existing parameters
        self.params_box.clear()

        if widget.value == "Remove Background":
            # Create a checkbox for background color fill
            self.checkbox = toga.Switch(
                'Fill Background Color',
                style=Pack(padding=(0, 10))
            )
            
            # Create a button to open the color picker
            self.color_button = toga.Button(
                'Select Color',
                on_press=self.open_color_picker,
                enabled=False,  # Initially disabled
                style=Pack(padding=(0, 10))
            )
            
            # Enable/disable color button based on checkbox
            def on_switch_change(switch):
                self.color_button.enabled = switch.value
            
            self.checkbox.on_change = on_switch_change
            
            # Add the switch and color button to the parameters box
            self.params_box.add(toga.Label('Parameters:', style=Pack(padding=(0, 10))))
            self.params_box.add(self.checkbox)
            self.params_box.add(self.color_button)
        else:
            pass

    async def handle_processing(self, widget):
        """Handle image processing"""
        selected_option = self.dropdown.value
        print(f'Processing image with option: {selected_option}')
        
        if selected_option == "Remove Background":
            await self.process_remove_background()
        elif selected_option == "Enhance Image":
            await self.process_enhance()
        else:
            print("Invalid option selected")

    async def process_remove_background(self):
        """Process image to remove background"""
        try:
            # Get original image path
            original_image = self.original_image_box.children[0].image
            input_path = original_image.path
            
            # Get background color settings
            use_bgcolor = self.checkbox.value if hasattr(self, 'checkbox') else False
            bgcolor = self.selected_color if (hasattr(self, 'selected_color') and use_bgcolor) else None

            # Process image
            with open(input_path, 'rb') as input_file:
                input_data = input_file.read()
                output_data = remove(input_data, bgcolor=bgcolor if use_bgcolor else None)
            
            # Save and display processed image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(output_data)
                output_path = temp_file.name

            # Wait a brief moment to ensure file is written
            await asyncio.sleep(0.1)

            self.display_image(output_path, self.processed_image_box)
                
            # Store the processed image path and enable download button
            self.processed_image_path = output_path
            self.download_button.enabled = True

        except Exception as e:
            print(f'Error processing image: {e}')
            # Print more detailed error information
            import traceback
            traceback.print_exc()


    async def process_enhance(self):
        """Process image enhancement"""

        try:
            # Get original image path
            original_image = self.original_image_box.children[0].image
            input_path = original_image.path
            
            # Open the image with PIL
            img = Image.open(input_path)
            
            # Step 1: Color Enhancement
            color_enhancer = ImageEnhance.Color(img)
            img = color_enhancer.enhance(1.2)  # Increase color saturation by 20%
            
            # Step 2: Contrast Enhancement
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(1.1)  # Increase contrast by 10%
            
            # Step 3: Brightness Enhancement
            brightness_enhancer = ImageEnhance.Brightness(img)
            img = brightness_enhancer.enhance(1.1)  # Increase brightness by 10%
            
            # Step 4: Sharpness Enhancement
            sharpness_enhancer = ImageEnhance.Sharpness(img)
            img = sharpness_enhancer.enhance(1.3)  # Increase sharpness by 30%
            
            # Step 5: Noise Reduction (Optional)
            img = img.filter(ImageFilter.SMOOTH_MORE)
            
            # Save the processed image to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                output_path = temp_file.name
                img.save(output_path, format='PNG')
                
                    # Ensure file exists and is accessible
            if os.path.exists(output_path):
                # Wait a brief moment to ensure file is written
                await asyncio.sleep(0.5)
                
                # Display the processed image
                self.display_image(output_path, self.processed_image_box)
                
                # Store the processed image path and enable download button
                self.processed_image_path = output_path
                self.download_button.enabled = True
            else:
                raise Exception("Failed to save processed image")
                
        except Exception as e:
            print(f'Error processing image: {e}')
            import traceback
            traceback.print_exc()


            
def main():
    return ImageMagic()