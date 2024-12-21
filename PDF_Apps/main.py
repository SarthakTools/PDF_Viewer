import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF for rendering PDF pages as images
import os

class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Viewer")
        self.root.geometry("800x600")
        self.root.state("zoomed")  # Maximize window
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("dark-blue")  # Dark blue theme

        self.pdf_pages = []
        self.current_page = 0
        self.zoom_factor = 1.0  # Initial zoom factor
        self.is_zoomed = False  # Track whether zoom is applied or not
        self.title_text = ""  # Variable to store the title of the PDF

        # Frame for buttons and page number
        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(fill="x", pady=10)

        # Open PDF Button
        self.open_button = ctk.CTkButton(self.button_frame, text="Open PDF", command=self.load_pdf, font=("Consolas", 20))
        self.open_button.pack(side="left", padx=10, pady=2, ipady=7, ipadx=5)

        # Title Label (middle of the button frame, right of Open PDF)
        self.title_label = ctk.CTkLabel(self.button_frame, text=self.title_text, font=("Arial", 20, "bold"), bg_color="transparent", text_color="white")
        self.title_label.pack(side="left", padx=20, pady=5, ipadx=10)

        # Load left and right arrow images
        self.left_image = self.load_image("images/left.png", (40, 40))
        self.right_image = self.load_image("images/right.png", (40, 40))

        # Reverse the order of buttons and remove text
        self.next_button = ctk.CTkButton(self.button_frame, image=self.right_image, text="", command=self.next_page, width=40, height=40)
        self.next_button.pack(side="right", padx=10, pady=10)

        self.prev_button = ctk.CTkButton(self.button_frame, image=self.left_image, text="", command=self.previous_page, width=40, height=40)
        self.prev_button.pack(side="right", padx=10, pady=10)

        # Label for page number
        self.page_label = ctk.CTkLabel(self.button_frame, text="1/1 pages", bg_color="black", text_color="white", font=("Arial", 18))
        self.page_label.pack(side="right", padx=10, pady=5, ipadx=10, ipady=5)

        # Canvas to display PDF
        self.canvas_frame = ctk.CTkFrame(self.root)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#2c2c2c", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add scrollbar
        self.scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind double-click to toggle zoom
        self.canvas.bind("<Button-1>", self.toggle_zoom)

        # Bind mouse wheel to scroll functionality
        self.canvas.bind_all("<MouseWheel>", self.mouse_scroll_pdf)

    def load_image(self, path, size):
        """Load and resize an image."""
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    def load_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            self.pdf_pages = self.extract_pages(filepath)
            self.current_page = 0
            self.zoom_factor = 1.0  # Reset zoom when opening a new PDF
            self.is_zoomed = False  # Reset zoom status
            self.title_text = self.extract_pdf_title(filepath)  # Extract and set title
            self.update_title_label()  # Update the title label
            self.display_page()

    def extract_pdf_title(self, filepath):
        """Extract title from PDF metadata or use filename as fallback."""
        pdf_document = fitz.open(filepath)
        metadata = pdf_document.metadata
        title = metadata.get("title", None)
        if not title:
            title = os.path.basename(filepath)  # Fallback to filename if no title
        # Limit the title length and add "..." if it's too long
        if len(title) > 30:
            title = title[:30] + "..."
        return title

    def update_title_label(self):
        """Update the title label with the extracted title."""
        self.title_label.configure(text=f"{self.title_text}.pdf")

    def extract_pages(self, filepath):
        """Extract and render PDF pages."""
        pdf_document = fitz.open(filepath)
        pages = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        return pages

    def display_page(self):
        """Display the current page on the canvas."""
        if self.pdf_pages:
            img = self.pdf_pages[self.current_page]

            # Resize to fit the window considering the zoom factor
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_ratio = img.width / img.height
            canvas_ratio = canvas_width / canvas_height

            if img_ratio > canvas_ratio:
                new_width = int(canvas_width * self.zoom_factor)
                new_height = int(new_width / img_ratio)
            else:
                new_height = int(canvas_height * self.zoom_factor)
                new_width = int(new_height * img_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(img)

            # Clear canvas and display image in the center
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width // 2, canvas_height // 2, anchor="center", image=self.tk_image)

            # Update page number label
            self.page_label.configure(text=f"{self.current_page + 1}/{len(self.pdf_pages)} pages")

            # Adjust scroll region dynamically
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Adjust the scrollbar to work with the new size
            self.scrollbar.configure(command=self.canvas.yview)

    def next_page(self):
        """Go to the next page."""
        if self.pdf_pages and self.current_page < len(self.pdf_pages) - 1:
            self.current_page += 1
            self.display_page()

    def previous_page(self):
        """Go to the previous page."""
        if self.pdf_pages and self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def toggle_zoom(self, event):
        """Toggle zoom on double-click."""
        if not self.is_zoomed:
            self.zoom_factor = 1.5  # Zoom in
            self.is_zoomed = True
        else:
            self.zoom_factor = 1.0  # Zoom out to normal size
            self.is_zoomed = False
        self.display_page()

    def mouse_scroll_pdf(self, event):
        """Scroll the PDF using the mouse wheel."""
        if event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, "units")

# Run the application
app_root = ctk.CTk()
app = PDFViewerApp(app_root)
app_root.mainloop()
