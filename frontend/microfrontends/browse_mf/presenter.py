from frontend.microfrontends.browse_mf.view import BrowseView
from models.api_client import ApiClient

class BrowsePresenter:
    def __init__(self, api_client: ApiClient):
        # Create instance of the view
        self.view = BrowseView()
        self.api_client = api_client
        
        # Connect events: click on the search button or enter on the keyboard
        self.view.search_button.clicked.connect(self.handle_search)
        self.view.search_input.returnPressed.connect(self.handle_search)

    def handle_search(self):
        # 1. Get the text from the search input
        query = self.view.search_input.text().strip()
        if not query:
            return

        # 2. Clear the old list for new results
        self.view.movies_list.clear()
        
        # 3. Request movies from the server using the ApiClient we set up earlier
        results = self.api_client.search_movies(query)
        
        # 4. Display the results on the screen
        for movie in results:
            display_text = f"{movie.title} ({movie.vote_average}★)"
            self.view.movies_list.addItem(display_text)