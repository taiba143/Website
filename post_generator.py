import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import json
import os
from datetime import datetime

# --- Configuration ---
# Make sure these paths are correct relative to where you run the script.
POSTS_JSON_PATH = 'posts.json'
BLOGPOSTS_FOLDER = 'blogposts'

# --- HTML Template for New Blog Posts ---
# This template will be used to generate the new .html files.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Abundant Coaches Hub</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
        }}
    </style>
</head>
<body class="bg-gray-50">
    <header class="bg-white shadow-sm">
        <nav class="container mx-auto px-6 py-4">
            <div class="text-2xl font-bold text-gray-900"><a href="../index.html">Abundant Coaches Hub</a></div>
        </nav>
    </header>

    <main class="container mx-auto px-6 py-12 max-w-3xl">
        <article>
            <h1 class="text-4xl font-extrabold text-gray-900">{title}</h1>
            <p class="text-lg text-gray-500 mt-2">{date} • {category}</p>
            
            <img class="w-full h-auto rounded-lg my-8 shadow-lg" src="{image_url}" alt="{title}">

            <div class="prose lg:prose-xl text-gray-700">
                {content}
            </div>
        </article>
    </main>

    <footer class="bg-white text-gray-700 mt-16">
        <div class="container mx-auto px-6 py-8 text-center">
            <p>© 2025 Abundant Coaches Hub. All Rights Reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

class BlogTool(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Blog Post Generator")
        self.setGeometry(100, 100, 850, 750)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Helvetica;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #e11d48;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c11b40;
            }
        """)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Grid Layout for Form Fields ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        self.fields = {}
        labels = ["Title", "Category", "Image URL", "Description", "Popularity (1-100)"]

        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            entry = QLineEdit()
            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(entry, i, 1)
            self.fields[label_text] = entry

        # --- Content Text Area ---
        content_label = QLabel("Content (HTML)")
        self.content_text = QTextEdit()
        grid_layout.addWidget(content_label, len(labels), 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(self.content_text, len(labels), 1)
        
        # Set row stretch to make the text area expandable
        grid_layout.setRowStretch(len(labels), 1)
        grid_layout.setColumnStretch(1, 1)

        main_layout.addLayout(grid_layout)

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        button_layout.addStretch(1) # Pushes the button to the right
        add_button = QPushButton("Add Post")
        add_button.clicked.connect(self.add_post)
        button_layout.addWidget(add_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def add_post(self):
        """Handles the logic for adding a new blog post."""
        
        post_data = {
            "title": self.fields["Title"].text(),
            "category": self.fields["Category"].text(),
            "image": self.fields["Image URL"].text(),
            "description": self.fields["Description"].text(),
            "content": self.content_text.toPlainText().strip()
        }

        if not all([post_data["title"], post_data["category"], post_data["description"], post_data["content"]]):
            QMessageBox.critical(self, "Error", "Please fill in all fields.")
            return

        try:
            popularity = int(self.fields["Popularity (1-100)"].text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Popularity must be a number.")
            return

        try:
            with open(POSTS_JSON_PATH, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            posts = []

        new_id = max([post.get('id', 0) for post in posts] + [0]) + 1
        
        new_post_entry = {
            "id": new_id,
            "image": post_data["image"],
            "date": datetime.now().strftime("%B %d, %Y"),
            "category": post_data["category"],
            "title": post_data["title"],
            "description": post_data["description"],
            "url": f"{BLOGPOSTS_FOLDER}/post{new_id}.html",
            "popularity": popularity
        }
        posts.append(new_post_entry)

        if not os.path.exists(BLOGPOSTS_FOLDER):
            os.makedirs(BLOGPOSTS_FOLDER)
            
        html_content = HTML_TEMPLATE.format(
            title=post_data["title"],
            date=new_post_entry["date"],
            category=post_data["category"],
            image_url=post_data["image"],
            content=post_data["content"]
        )
        
        file_path = os.path.join(BLOGPOSTS_FOLDER, f"post{new_id}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        with open(POSTS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2)

        QMessageBox.information(self, "Success", f"Post '{post_data['title']}' was added successfully!\nFile created at: {file_path}")
        self.clear_fields()

    def clear_fields(self):
        """Clears all input fields after a successful submission."""
        for entry in self.fields.values():
            entry.clear()
        self.content_text.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = BlogTool()
    tool.show()
    sys.exit(app.exec())
