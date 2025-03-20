# Movie Agent Example :material-movie-outline:

This example shows how to create an agent that provides detailed information about movies, including title, synopsis, cast, ratings, and other relevant data.

## Agent Definition

Create a file called `agent_definition.yaml`:

```yaml
agents:
  movie_agent:
    credentials:
      - movies_api_key:
          - label: "api movies"
          - placeholder: "movies_api_key"
    name: "Movie Agent"
    description: "Expert in searching for movie information"
    instructions:
        - "You are an expert in searching for detailed information about movies"
        - "When the user asks about a movie, you should search and present the most relevant information"
        - "If the user provides the movie title in Portuguese, you should translate it to English before searching"
        - "The API returns information in English, and you should translate the overview to Portuguese naturally and fluently"
        - "Keep original titles in English, but you can provide an informal translation in parentheses when relevant"
        - "If you can't find the movie, suggest similar titles"
        - "Remember that the search must be done in English, even if the user asks in Portuguese"
        - "When translating the overview, maintain the tone and style of the original text, adapting only to Brazilian Portuguese"
        - "When translating the movie title to English, use the most common and internationally recognizable name"
    guardrails:
        - "Maintain a professional and informative tone when presenting movies"
        - "Don't make assumptions about movie content"
        - "Provide accurate and verified information"
        - "When translating, maintain fidelity to the original text meaning"
        - "If there's doubt in title translation, use the most internationally known name"
    skills:
    - get_movies_new:
        name: "Search Movies New"
        source:
          path: "skills/get_movies"
          entrypoint: "main.GetMovies"
          path_test: "test_definition.yaml"
        description: "Function to search for movie information"
        parameters:
            - movie_title:
                description: "movie title to search for (will be translated to English if in Portuguese)"
                type: "string"
                required: true
                contact_field: true
```

## Skill Implementation

Create a file `skills/get_movies/main.py`:

```python
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse
import requests
from datetime import datetime


class GetMovies(Skill):
    def execute(self, context: Context) -> TextResponse:
        movie_title = context.parameters.get("movie_title", "")
        api_key = context.credentials.get("movies_api_key")
        
        # Search for movies by title
        movies_response = self.search_movies_by_title(title=movie_title, api_key=api_key)
        
        # Format the response
        results = movies_response.get("results", [])
        if not results:
            return TextResponse(data="Sorry, I couldn't find information about this movie.")
        
        # Get the first (most relevant) movie
        movie_id = results[0].get("id")
        
        # Get detailed information about the movie
        movie_details = self.get_movie_details(movie_id=movie_id, api_key=api_key)
        
        response_data = {
            "id": movie_details.get("id"),
            "title": movie_details.get("title"),
            "original_title": movie_details.get("original_title"),
            "tagline": movie_details.get("tagline"),
            "overview": movie_details.get("overview"),
            "release_date": movie_details.get("release_date"),
            "runtime": movie_details.get("runtime"),
            "vote_average": movie_details.get("vote_average"),
            "vote_count": movie_details.get("vote_count"),
            "genres": movie_details.get("genres", []),
            "poster_path": f"https://image.tmdb.org/t/p/w500{movie_details.get('poster_path')}" if movie_details.get("poster_path") else None,
            "backdrop_path": f"https://image.tmdb.org/t/p/original{movie_details.get('backdrop_path')}" if movie_details.get("backdrop_path") else None
        }
        
        return TextResponse(data=response_data)

    def search_movies_by_title(self, title, api_key):
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": api_key,
            "query": title,
            "language": "en-US",
            "page": 1
        }
        response = requests.get(url, params=params)
        return response.json()
        
    def get_movie_details(self, movie_id, api_key):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {
            "api_key": api_key,
            "language": "en-US",
            "append_to_response": "credits,similar"
        }
        response = requests.get(url, params=params)
        return response.json()
```

Create a file `skills/get_movies/requirements.txt`:

```
requests==2.32.3
```

Create a file `skills/get_movies/test_definition.yaml`:

```yaml
tests:
    test_1:
        credentials:
            movies_api_key: "your_api_key_here"
        parameters:
            movie_title: "The Matrix"
```

## Getting Credentials

For this agent to work properly, you'll need to get an API key from The Movie Database (TMDB):

1. Visit the [TMDB](https://www.themoviedb.org/) website
2. Register for a free account
3. Access the API section in your account and request an API key
4. Copy your API key
5. When deploying the agent, you'll need to provide this key as a credential

## Testing the Skill Locally

Before deploying your agent, you can test the skill locally using the `weni run` command. This allows you to verify that your skill works correctly and debug any issues.

Since this skill requires credentials, you'll need to create a `.env` file in the root of your project with your TMDB API key:

```
movies_api_key=your_actual_tmdb_api_key_here
```

To test the Movie Agent skill:

```bash
weni run agent_definition.yaml movie_agent get_movies_new
```

This command will execute the tests defined in the `test_definition.yaml` file and show you the output. The CLI will automatically pick up the credentials from the `.env` file and make them available to your skill during execution.

If you need more detailed logs for debugging, you can add the `-v` flag:

```bash
weni run agent_definition.yaml movie_agent get_movies_new -v
```

The verbose output will show you more details about the execution process, including API requests and responses, helping you identify and fix any issues with your skill.

## Deployment Steps

1. Deploy the agent:
   ```bash
   weni project push agent_definition.yaml
   ```

## Testing

After deployment, you can test the agent:

1. Open your project in the Weni platform
2. Find the Movie Agent in your agents list
3. Provide the TMDB API key in the credential settings
4. Start a conversation
5. Send a movie title in Portuguese or English (e.g., "The Godfather" or "Pulp Fiction")

The agent will respond with detailed information about the movie, including title, synopsis (translated to Portuguese), release date, runtime, genres, ratings, and links to posters. If the title is provided in Portuguese, the agent will automatically translate it to perform the search. 