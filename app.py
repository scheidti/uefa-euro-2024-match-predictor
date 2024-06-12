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

        for i in range(1, 3):
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
                games_result.append(
                    {"team1": team1, "team2": team2, "result": result_text}
                )
        except Exception as e:
            print(e)
            return None
        
        return games_result


matches = get_matches()
matches = [match for match in matches if not match["matchIsFinished"]]

if len(matches) > 0:
    match = matches[0]
    team1_id = match["team1"]["teamId"]
    team2_id = match["team2"]["teamId"]
    team1_name = match["team1"]["teamName"]
    team2_name = match["team2"]["teamName"]
 
    # maybe games_stats_url is not needed, games_data_url is enough for now
    games_stats_url = f"https://api.openligadb.de/getmatchdata/{team1_id}/{team2_id}"
    games_data_url = f"https://www.fussballdaten.de/vereine/{translate_umlauts(team1_name)}/{translate_umlauts(team2_name)}/spiele/"

    # TODO: Search for news about the teams

    print(f"{team1_name} vs. {team2_name}")
    print(games_data_url)
    rankings = get_ranking()
    print(rankings)
    # latest game is the first one, can be None on error
    games = get_games_by_teams(games_data_url)
    print(games)
