# Book Agent Example :material-book-open-variant:

This example shows how to create an agent that provides detailed information about books based on the title provided by the user.

## Agent Definition

Create a file called `agent_definition.yaml`:

```yaml
agents:
    book_agent:
      name: "Book Agent"
      description: "Expert in searching for book information"
      instructions:
        - "You are an expert in searching for detailed information about books"
        - "When the user asks about a book, you should search and present the most relevant information"
        - "The API returns information in English, and you should translate the description to Portuguese naturally and fluently"
        - "If you can't find the book, suggest similar titles"
        - "When translating the description, maintain the tone and style of the original text, adapting only to Brazilian Portuguese"
        - "Provide information about authors, publisher, publication date, page count, and ratings when available"
        - "You must translate the book description to Portuguese before presenting it to the user"
      guardrails:
        - "Maintain a professional and informative tone when presenting books"
        - "Don't make assumptions about book content"
        - "Provide accurate and verified information"
        - "When translating, maintain fidelity to the original text meaning"
        - "Mention when rating or page count information is not available"
      skills:
      - get_books:
          name: "Search Books"
          source:
            path: "skills/get_books"
            entrypoint: "books.GetBooks"
            path_test: "test_definition.yaml"
          description: "Function to search for book information"
          parameters:
            - book_title:
                description: "book title to search for"
                type: "string"
                required: true
                contact_field: true
```

## Skill Implementation

Create a file `skills/get_books/books.py`:

```python
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse
import requests
from datetime import datetime


class GetBooks(Skill):
    def execute(self, context: Context) -> TextResponse:
        apiKey = context.credentials.get("apiKey")
        
        book_title = context.parameters.get("book_title", "")
        books_response = self.get_books_by_title(title=book_title)
        
        # Format the response
        items = books_response.get("items", [])
        if not items:
            return TextResponse(data="Sorry, I couldn't find information about this book.")
        
        response_data = {
            "status": "success",
            "totalResults": len(items[:5]),
            "books": []
        }
        
        for book in items[:5]:
            volume_info = book.get("volumeInfo", {})
            book_data = {
                "id": book.get("id"),
                "title": volume_info.get("title"),
                "authors": volume_info.get("authors", []),
                "publisher": volume_info.get("publisher"),
                "publishedDate": volume_info.get("publishedDate"),
                "description": volume_info.get("description", ""),
                "pageCount": volume_info.get("pageCount"),
                "categories": volume_info.get("categories", []),
                "averageRating": volume_info.get("averageRating"),
                "ratingsCount": volume_info.get("ratingsCount"),
                "imageLinks": volume_info.get("imageLinks", {}),
                "language": volume_info.get("language"),
                "previewLink": volume_info.get("previewLink"),
                "infoLink": volume_info.get("infoLink")
            }
            response_data["books"].append(book_data)
            
        return TextResponse(data=response_data)

    def get_books_by_title(self, title):
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            "q": title
        }
        response = requests.get(url, params=params)
        return response.json()
```

Create a file `skills/get_books/requirements.txt`:

```
requests==2.32.3
```

Create a file `skills/get_books/test_definition.yaml`:

```yaml
tests:
    test_1:
        parameters:
            book_title: "The Hobbit"
```

## Testing the Skill Locally

Before deploying your agent, you can test the skill locally using the `weni run` command. This allows you to verify that your skill works correctly and debug any issues.

To test the Book Agent skill:

```bash
weni run agent_definition.yaml book_agent get_books
```

This command will execute the tests defined in the `test_definition.yaml` file and show you the output. You should see the book information for "The Hobbit" test case.

If you need more detailed logs for debugging, you can add the `-v` flag:

```bash
weni run agent_definition.yaml book_agent get_books -v
```

The verbose output will show you more details about the execution process, helping you identify and fix any issues with your skill.

## Deployment Steps

1. Deploy the agent:
   ```bash
   weni project push agent_definition.yaml
   ```

## Testing

After deployment, you can test the agent:

1. Open your project in the Weni platform
2. Find the Book Agent in your agents list
3. Start a conversation
4. Send a book title (e.g., "Pride and Prejudice" or "Harry Potter")

The agent will respond with detailed information about the book, including title, authors, publisher, publication date, page count, and ratings when available. The book description will be automatically translated to Portuguese. 