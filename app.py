import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

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
                news_result.append({"url": news_url, "text": news_text, "title": news_titles.pop(0)})
            except Exception as e:
                print(e)

    return news_result


matches = get_matches()
matches = [match for match in matches if not match["matchIsFinished"]]

if len(matches) > 0:
    match = matches[0]
    team1_id = match["team1"]["teamId"]
    team2_id = match["team2"]["teamId"]
    team1_name = match["team1"]["teamName"]
    team2_name = match["team2"]["teamName"]
    games_data_url = f"https://www.fussballdaten.de/vereine/{translate_umlauts(team1_name)}/{translate_umlauts(team2_name)}/spiele/"

    rankings = get_ranking()
    games = get_games_by_teams(games_data_url)
    tagesschau_news = get_news_tagesschau(team1_name, team2_name)
