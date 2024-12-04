##=============================================================================
# Magic Image Processing Tool
#
# History
# When      | Who        | What
# ----------|------------|-------------------------
# 03/12/2024| TQ Ye      | First version
##=============================================================================
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2  # For advanced image processing
import numpy as np  # For array operations
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
        # Create main box
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=8))
        
        # Create scroll container
        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.scroll_container.content = self.main_box
        
        # Setup components and window
        self.setup_ui_components()
        self.setup_window()

    def setup_ui_components(self):
        """Setup all UI components"""
        #self.create_title()
        self.create_upload_section()
        self.create_processing_section()
        self.create_image_display_section()
        
        # Add all components to main box
        #self.main_box.add(self.title_label)
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
        self.main_window.content = self.scroll_container  # Use scroll container instead of main_box
        self.main_window.show()

    def create_upload_section(self):
        """Create the upload button and related functionality"""
        self.upload_button = toga.Button(
            'Upload Image',
            on_press=self.handle_file_upload,
            style=Pack(padding=8)
        )

    def create_processing_section(self):
        """Create the processing options and button"""
        # Create processing options box
        self.proc_option_box = toga.Box(style=Pack(direction=ROW, padding=8))
        
        # Add dropdown label and list
        dropdown_label = toga.Label(
            'Choose Processing:',
            style=Pack(padding=(0, 8, 0, 0))
        )
        
        self.dropdown = toga.Selection(
            items=['Remove Background', 'Enhance Image', 'Artistic Filters', 'Object Removal'],
            on_select=self.handle_option_select,
            style=Pack(flex=1)
        )
        
        # Create parameters box
        self.params_box = toga.Box(style=Pack(direction=ROW, padding=6))
    
        self.proc_option_box.add(dropdown_label)
        self.proc_option_box.add(self.dropdown)
        
        # Create process button
        self.process_button = toga.Button(
            'Process Image',
            on_press=self.handle_processing,
            enabled=False,
            style=Pack(padding=6)
        )

    def create_image_display_section(self):
        """Create the image display section"""
        self.image_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Create a row for images
        image_row = toga.Box(style=Pack(direction=ROW))

        # Original image section
        original_section = toga.Box(style=Pack(direction=COLUMN, padding=6))
        original_label = toga.Label(
            'Original Image:',
            style=Pack(padding=(0, 0, 4, 0))
        )
        self.original_image_box = toga.Box(style=Pack(padding=6))
        original_section.add(original_label)
        original_section.add(self.original_image_box)
        
        # Processed image section
        processed_section = toga.Box(style=Pack(direction=COLUMN, padding=6))
        processed_label = toga.Label(
            'Processed Image:',
            style=Pack(padding=(0, 0, 4, 0))
        )
        self.processed_image_box = toga.Box(style=Pack(padding=6))
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
            style=Pack(padding=8)
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
            padding=4
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
                style=Pack(padding=(0, 8))
            )
            
            # Create a button to open the color picker
            self.color_button = toga.Button(
                'Select Color',
                on_press=self.open_color_picker,
                enabled=False,  # Initially disabled
                style=Pack(padding=(0, 8))
            )
            
            # Enable/disable color button based on checkbox
            def on_switch_change(switch):
                self.color_button.enabled = switch.value
            
            self.checkbox.on_change = on_switch_change
            
            # Add the switch and color button to the parameters box
            self.params_box.add(toga.Label('Parameters:', style=Pack(padding=(0, 10))))
            self.params_box.add(self.checkbox)
            self.params_box.add(self.color_button)
        elif widget.value == "Enhance Image":
            # Set params_box to use column direction
            self.params_box.style.update(direction=COLUMN)
            
            # Create parameters label
            params_label = toga.Label(
                'Enhancement Parameters:',
                style=Pack(padding=(0, 0, 6, 0))
            )
            self.params_box.add(params_label)

            # Function to create a parameter row
            def create_param_row(label_text, default_value):
                row = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
                label = toga.Label(label_text, style=Pack(padding=(0, 6), width=100))
                number_input = toga.NumberInput(
                    min_value=0.0,
                    max_value=2.0,
                    value=default_value,
                    step=0.1,
                    style=Pack(width=70)
                )
                row.add(label)
                row.add(number_input)
                return row, number_input

            # Create parameter rows
            color_row, self.color_input = create_param_row('Color:', 1.2)
            contrast_row, self.contrast_input = create_param_row('Contrast:', 1.1)
            brightness_row, self.brightness_input = create_param_row('Brightness:', 1.1)
            sharpness_row, self.sharpness_input = create_param_row('Sharpness:', 1.3)
            
            # Create noise reduction row
            noise_row = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
            noise_label = toga.Label('Noise Reduction:', style=Pack(padding=(0, 10), width=100))
            self.noise_reduction = toga.Switch(
                'Apply',
                value=True,
                style=Pack(padding=(0, 6))
            )
            noise_row.add(noise_label)
            noise_row.add(self.noise_reduction)
            
            # Add all rows to params box
            self.params_box.add(color_row)
            self.params_box.add(contrast_row)
            self.params_box.add(brightness_row)
            self.params_box.add(sharpness_row)
            self.params_box.add(noise_row)
        elif widget.value == "Artistic Filters":
            # Set params_box to use column direction
            self.params_box.style.update(direction=COLUMN)
            
            # # Create parameters label
            # params_label = toga.Label(
            #     'Filter Parameters:',
            #     style=Pack(padding=(0, 0, 6, 0))
            # )
            # self.params_box.add(params_label)

            # Create filter selection row
            filter_row = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
            filter_label = toga.Label('Filter:', style=Pack(padding=(0, 8), width=100))
            self.filter_select = toga.Selection(
                items=['Grayscale', 'Sepia', 'Blur', 'Emboss', 'Edge Enhance', 'Posterize', 'Negative'],
                style=Pack(width=150)
            )
            filter_row.add(filter_label)
            filter_row.add(self.filter_select)
            
            # Create intensity control row
            intensity_row = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
            intensity_label = toga.Label('Intensity:', style=Pack(padding=(0, 10), width=100))
            self.intensity_input = toga.NumberInput(
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.1,
                style=Pack(width=70)
            )
            intensity_row.add(intensity_label)
            intensity_row.add(self.intensity_input)
            
            # Add rows to params box
            self.params_box.add(filter_row)
            self.params_box.add(intensity_row)            
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
        elif selected_option == "Artistic Filters":
            await self.process_artistic_filter()
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
        """
        Process image enhancement
        """
        try:
            # Get original image path
            original_image = self.original_image_box.children[0].image
            input_path = original_image.path
            
            # Open the image with PIL
            img = Image.open(input_path)
            
            # Get enhancement parameters from number inputs
            color_value = self.color_input.value
            contrast_value = self.contrast_input.value
            brightness_value = self.brightness_input.value
            sharpness_value = self.sharpness_input.value
            apply_noise_reduction = self.noise_reduction.value
            
            # Step 1: Color Enhancement
            color_enhancer = ImageEnhance.Color(img)
            img = color_enhancer.enhance(color_value)
            
            # Step 2: Contrast Enhancement
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(contrast_value)
            
            # Step 3: Brightness Enhancement
            brightness_enhancer = ImageEnhance.Brightness(img)
            img = brightness_enhancer.enhance(brightness_value)
            
            # Step 4: Sharpness Enhancement
            sharpness_enhancer = ImageEnhance.Sharpness(img)
            img = sharpness_enhancer.enhance(sharpness_value)
            
            # Step 5: Noise Reduction (Optional)
            if apply_noise_reduction:
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

    async def process_artistic_filter(self):
        """Apply artistic filter to image"""
        try:
            # Get original image path
            original_image = self.original_image_box.children[0].image
            input_path = original_image.path
            
            # Open the image with PIL
            img = Image.open(input_path)
            
            # Get filter parameters
            filter_type = self.filter_select.value
            intensity = self.intensity_input.value
            
            # Apply selected filter
            if filter_type == 'Grayscale':
                img = ImageOps.grayscale(img)
                # Convert back to RGB mode for consistent handling
                img = img.convert('RGB')
                
            elif filter_type == 'Sepia':
                # Apply sepia filter
                width, height = img.size
                pixels = img.load()
                for x in range(width):
                    for y in range(height):
                        r, g, b = pixels[x, y]
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
                
            elif filter_type == 'Blur':
                # Apply Gaussian blur
                img = img.filter(ImageFilter.GaussianBlur(radius=intensity * 2))
                
            elif filter_type == 'Emboss':
                img = img.filter(ImageFilter.EMBOSS)
                
            elif filter_type == 'Edge Enhance':
                img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
                
            elif filter_type == 'Posterize':
                # Convert to RGB if not already
                img = img.convert('RGB')
                # Posterize effect (reduce number of colors)
                img = ImageOps.posterize(img, int(8 - (intensity * 3)))
                
            elif filter_type == 'Negative':
                img = ImageOps.invert(img)
            
            # Save the processed image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                output_path = temp_file.name
                img.save(output_path, format='PNG')
            
            # Ensure file exists and is accessible
            if os.path.exists(output_path):
                # Wait a bit longer to ensure file is fully written
                await asyncio.sleep(0.5)
                
                # Display the processed image
                self.display_image(output_path, self.processed_image_box)
                
                # Store the processed image path and enable download button
                self.processed_image_path = output_path
                self.download_button.enabled = True
            else:
                raise Exception("Failed to save processed image")
                
        except Exception as e:
            print(f'Error applying filter: {e}')
            import traceback
            traceback.print_exc()

################################################
def main():
    return ImageMagic()