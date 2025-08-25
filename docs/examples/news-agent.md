# News Agent Example :material-newspaper-variant-outline:

This example shows how to create an agent that provides up-to-date news on various topics through a news API.

## Agent Definition

Create a file called `agent_definition.yaml`:

```yaml
agents:
    news_agent:
        credentials:
            apiKey:
                label: "API Key"
                placeholder: "apiKey"
        name: "News Agent"
        description: "Expert in searching and providing news about any topic"
        instructions:
            - "You are an expert in searching and providing updated news about any topic"
            - "When the user asks about a topic, you should search and present the most relevant news"
            - "Always be helpful and provide brief context about the news found"
            - "If you can't find news about the topic, suggest related topics"
            - "Always use english to answer the user and be polite"
        guardrails:
            - "Maintain a professional and impartial tone when presenting news"
            - "Don't make assumptions or speculations about the news"
            - "Avoid sharing sensationalist or unverified news"
        tools:
        - get_news:
            name: "Get News"
            source:
                path: "tools/get_news"
                entrypoint: "main.GetNews"
                path_test: "test_definition.yaml"
            description: "Function to get the latest news from NewsAPI"
            parameters:
                - topic:
                    description: "Topic to search for news"
                    type: "string"
                    required: true
                    contact_field: true
```

## Tool Implementation

Create a file `tools/get_news/main.py`:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
from datetime import datetime


class GetNews(Tool):
    def execute(self, context: Context) -> TextResponse:
        apiKey = context.credentials.get("apiKey")
        
        topic = context.parameters.get("topic", "")
        news_response = self.get_news_by_topic(topic=topic, apiKey=apiKey)
        
        # Format the response
        articles = news_response.get("articles", [])
        if not articles:
            return TextResponse(data="Sorry, I couldn't find any news on this topic.")
        
        response_data = {
            "status": news_response.get("status"),
            "totalResults": len(articles[:10]),
            "articles": []
        }
        
        # Get only the first 10 articles
        for article in articles[:10]:
            article_data = {
                "source": article.get("source", {}),
                "author": article.get("author"),
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "urlToImage": article.get("urlToImage"),
                "publishedAt": article.get("publishedAt"),
                "content": article.get("content")
            }
            response_data["articles"].append(article_data)
            
        return TextResponse(data=response_data)

    def get_news_by_topic(self, topic, apiKey):
        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "sortBy": "popularity",
            "apiKey": apiKey,
            "language": "en"
        }
        response = requests.get(url, params=params)
        return response.json()
```

Create a file `tools/get_news/requirements.txt`:

```
requests==2.32.3
```

Create a file `tools/get_news/test_definition.yaml`:

```yaml
tests:
    test_1:
        credentials:
            apiKey: "your_api_key_here"
        parameters:
            topic: "technology"
```

## Getting Credentials

For this agent to work properly, you'll need to get an API key from News API:

1. Visit the [News API](https://newsapi.org/) website
2. Register for a free account
3. Copy your API key from your account
4. When deploying the agent, you'll need to provide this key as a credential

## Testing the Tool Locally

Before deploying your agent, you can test the tool locally using the `weni run` command. This allows you to verify that your tool works correctly and debug any issues.

Since this tool requires credentials, create a `.env` file in the tool folder with your API key (e.g., `tools/get_news/.env`):

```
apiKey=your_actual_news_api_key_here
```

To test the News Agent tool:

```bash
weni run agent_definition.yaml news_agent get_news
```

This command will execute the tests defined in the `test_definition.yaml` file and show you the output. The CLI will automatically pick up the credentials from the tool folder `.env` file and make them available to your tool during execution.

If you need more detailed logs for debugging, you can add the `-v` flag:

```bash
weni run agent_definition.yaml news_agent get_news -v
```

The verbose output will show you more details about the execution process, helping you identify and fix any issues with your tool.

## Deployment Steps

1. Deploy the agent:
   ```bash
   weni project push agent_definition.yaml
   ```

## Testing

After deployment, you can test the agent:

1. Open your project in the Weni platform
2. Find the News Agent in your agents list
3. Provide the News API key in the credential settings
4. Start a conversation
5. Send a topic to search for news (e.g., "technology", "sports", "business")

The agent will respond with the most relevant news about the requested topic, including title, description, source, author, publication date, and links to the full article. 