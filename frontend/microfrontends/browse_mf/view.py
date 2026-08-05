from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget

class BrowseView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Search area (top row)
        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a movie...")
        self.search_button = QPushButton("Search")
        
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.search_button)

        # Results area (list)
        self.movies_list = QListWidget()

        # Add to the main component's screen
        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.movies_list)