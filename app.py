import requests
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from openai import OpenAI

load_dotenv()

umlauts_char_map = {
    ord("ä"): "ae",
    ord("ü"): "ue",
    ord("ö"): "oe",
    ord("ß"): "ss",
    ord(" "): "-",
}


def get_matches():
    """Gets the matches of the UEFA Euro 2024."""
    response = requests.get("https://api.openligadb.de/getmatchdata/em/2024")
    return response.json()


def translate_umlauts(text):
    """Translates umlauts to their respective ASCII characters."""
    return text.lower().translate(umlauts_char_map)


def get_ranking():
    """Scrapes the FIFA world ranking from fussballdaten.de and returns the top 60 teams."""
    with sync_playwright() as pw:
        rankings = []
        chrome = pw.chromium.launch(headless=True)

        for i in range(1, 6):
            page_url = (
                f"https://www.fussballdaten.de/fifa-weltrangliste/?page={i}&per-page=30"
            )
            page = chrome.new_page()
            response = page.goto(page_url)

            if response.status != 200:
                continue

            try:
                page.wait_for_selector("div[class=content-tabelle]")
                soup = BeautifulSoup(page.content(), "html.parser")
                table = soup.select(".table-statistik tbody tr")

                for row in table:
                    rank = row.select_one("td:nth-child(1)").text
                    team = row.select_one("td:nth-child(2) a").text
                    points = row.select_one("td:nth-child(5)").text
                    rankings.append({"rank": rank, "team": team, "points": points})
            except Exception as e:
                print(e)

        return rankings


def get_games_by_teams(games_data_url):
    """Scrapes the games of the UEFA Euro 2024 from fussballdaten.de."""
    with sync_playwright() as pw:
        games_result = []
        chrome = pw.chromium.launch(headless=True)
        page = chrome.new_page()
        response = page.goto(games_data_url)

        if response.status != 200:
            return None

        try:
            page.wait_for_selector("div[id=spieleDaten]")
            soup = BeautifulSoup(page.content(), "html.parser")
            games = soup.select(".content-spiele.bilanz .content-spiele .spiele-row")

            for game in games:
                result = game.select_one(".ergebnis")

                if result is None:
                    continue

                team1 = game.select_one("a:nth-child(1)").text
                team2 = game.select_one("a:nth-child(3)").text
                result_text = game.select_one(".ergebnis span").text
                result_list = result_text.split(":")
                date_text = game.select_one(".fcgrey").text
                games_result.append(
                    {
                        "team1": team1,
                        "team2": team2,
                        "result": result_text,
                        "date": date_text,
                        "goals_team1": result_list[0],
                        "goals_team2": result_list[1],
                    }
                )
        except Exception as e:
            print(e)
            return None

        return games_result


def get_news_tagesschau(team1, team2):
    """Scrapes the news of the teams from Tagesschau."""
    news_result = []

    tagesschau_url = "https://www.tagesschau.de/api2/news/?ressort=sport"
    tagesschau_response = requests.get(tagesschau_url)
    tagesschau_json = tagesschau_response.json()

    news_urls = []
    news_titles = []

    for news in tagesschau_json["news"]:
        tag_contains_em = (
            len([tag for tag in news["tags"] if tag["tag"] == "EM 2024"]) > 0
        )
        title_contains_team1 = team1.lower() in news["title"].lower()
        title_contains_team2 = team2.lower() in news["title"].lower()
        if tag_contains_em and (title_contains_team1 or title_contains_team2):
            news_urls.append(news["detailsweb"])
            news_titles.append(news["title"])

    with sync_playwright() as pw:
        chrome = pw.chromium.launch(headless=True)

        for news_url in news_urls:
            page = chrome.new_page()
            response = page.goto(news_url)

            if response.status != 200:
                continue

            try:
                page.wait_for_selector("div[id=content]")
                soup = BeautifulSoup(page.content(), "html.parser")
                news_text = soup.select(".textabsatz")
                news_text = " ".join([text.text for text in news_text])
                news_result.append(
                    {"url": news_url, "text": news_text, "title": news_titles.pop(0)}
                )
            except Exception as e:
                print(e)

    return news_result


def get_bing_news(team1, team2):
    """Scrapes the news of the teams from Bing."""
    bing_url = "https://api.bing.microsoft.com/v7.0/search"
    subscription_key = os.environ["BING_KEY_1"]
    query = f"{team1} {team2} EM 2024"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    mkt = "de-DE"
    params = {"q": query, "mkt": mkt, "textFormat": "Raw", "count": 3}
    response = requests.get(bing_url, headers=headers, params=params)
    json = response.json()
    news_articles = json["news"]["value"]
    news_result = []

    for article in news_articles:
        news_result.append(
            {
                "url": article["url"],
                "title": article["name"],
                "description": article["description"],
            }
        )

    return news_result


def get_ranking_for_team(team, rankings):
    """Gets the FIFA world ranking for a specific team."""
    for rank in rankings:
        if rank["team"].lower() == team.lower():
            return rank["rank"]

    return None


def get_last_games_string(games):
    """Gets the last games of the teams as a string."""
    games_string = ""
    for game in games:
        games_string += f"{game['team1']} - {game['team2']}: {game['result']} ({game['date'].strip()})\n"

    return games_string


def get_tagesschau_news_string(news):
    """Gets the news from Tagesschau as a string."""
    news_string = ""
    for article in news:
        news_string += f"Titel: {article['title']}:\nText:{article['text']}\n\n"

    return news_string


def get_bing_news_string(news):
    """Gets the news from Bing as a string."""
    news_string = ""
    for article in news:
        news_string += f"Titel: {article['title']}\nBeschreibung: {article['description']}\nURL: {article['url']}\n\n"

    return news_string


def get_game_prediction(prompt):
    api_key = os.environ["OPEN_AI_KEY"]
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    print(completion.choices[0].message)


matches = get_matches()
matches = [match for match in matches if not match["matchIsFinished"]]
rankings = get_ranking()

prompt = """Du bist ein Experte für die Vorhersage der Fussballergebnisse der UEFA Euro 2024.
Wenn du die Ergebnisse der Spiele korrekt vorhersagst, gewinnst du 500 Euro.
Du sollst das Ergebnis des folgenden Spiels vorhersagen:

{0}

Das sind die letzen Ergebnisse der Spiele der beiden Teams:

{1}

Folgende News gibt es zu den Teams. Beziehe die News in deine Vorhersage mit ein, falls du die News für relevant hältst:

{2}

Hier hast du weitere News-Titel und eine kurze Beschreibung. Klicke auf den Link, um die vollständige News zu lesen.
Klicke nur auf den Link und lies die News, wenn du die News für relevant hältst:

{3}

Gib dein Ergebnis in der folgenden Form aus:

Tore Team 1 : Tore Team 2

Viel Erfolg! 🍀
"""

if len(matches) > 0:
    match = matches[0]
    team1_id = match["team1"]["teamId"]
    team2_id = match["team2"]["teamId"]
    team1_name = match["team1"]["teamName"]
    team2_name = match["team2"]["teamName"]
    team1_rank = get_ranking_for_team(team1_name, rankings)
    team2_rank = get_ranking_for_team(team2_name, rankings)
    games_data_url = f"https://www.fussballdaten.de/vereine/{translate_umlauts(team1_name)}/{translate_umlauts(team2_name)}/spiele/"

    games = get_games_by_teams(games_data_url)
    match_string = f"{team1_name} (FIFA-Weltranglisten-Rang: {team1_rank}) vs {team2_name} (FIFA-Weltranglisten-Rang: {team2_rank})"
    games_string = get_last_games_string(games)
    tagesschau_news = get_news_tagesschau(team1_name, team2_name)
    tagesschau_news_string = get_tagesschau_news_string(tagesschau_news)
    bing_news = get_bing_news(team1_name, team2_name)
    bing_news_string = get_bing_news_string(bing_news)

    get_game_prediction(
        prompt.format(
            match_string, games_string, tagesschau_news_string, bing_news_string
        )
    )
