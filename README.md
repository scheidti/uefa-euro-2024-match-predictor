# UEFA Euro 2024 Match Predictor

This Python script predicts the results of the next upcoming UEFA Euro 2024 matches using the OpenAI GPT-4 model. It utilizes various data sources, including match data, FIFA world rankings, and news articles, to make informed predictions.

## Features

- Fetches upcoming match data for UEFA Euro 2024.
- Scrapes FIFA world rankings to consider team strengths.
- Gathers recent games data between the teams for historical context.
- Scrapes news from Tagesschau and Bing to include recent developments.
- Predicts match outcomes using the OpenAI GPT-4 model with a detailed prompt in German.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8 or higher
- `requests`, `typer`, `python-dotenv`, `playwright`, `beautifulsoup4`, and `openai` Python packages
- A Bing Search API key and an OpenAI API key set as environment variables (`BING_KEY` and `OPEN_AI_KEY`)

## Installation

1. Clone the repository to your local machine.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Install the Playwright browsers:

```bash
playwright install
```

4. Set your Bing Search API key and OpenAI API key as environment variables:

Copy the `.env.example` file to a new file named `.env` and fill in your Bing Search API key and OpenAI API key:

```bash
BING_KEY="your_bing_api_key"
OPEN_AI_KEY='"your_openai_api_key"
```

## Usage

Run the script from the command line, specifying the number of matches you want to predict:

```bash
python main.py [number_of_matches]
```

For example, to predict the next 3 matches:

```bash
python main.py 3
```

## License

This project is open-source and available under the [MIT License](LICENSE).
```