import os
import requests
import time
import logging
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from transformers import pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_schedule(date):
    base_url = "https://statsapi.mlb.com/api/v1"
    schedule_endpoint = f"/schedule?date={date}&sportId=1"
    url = f"{base_url}{schedule_endpoint}"
    logging.info(f"Requesting schedule from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Schedule fetched successfully")
        return response.json()
    else:
        logging.error(f"Error: Unable to fetch schedule. Status code: {response.status_code}")
        logging.error(f"Response content: {response.text}")
        return None

def get_detailed_game_data(game_pk):
    base_url = "https://statsapi.mlb.com/api/v1.1"
    game_endpoint = f"/game/{game_pk}/feed/live"
    url = f"{base_url}{game_endpoint}"
    logging.info(f"Requesting game data from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Game data fetched successfully")
        data = response.json()
        result = {
            'game_info': get_game_info(data),
            'linescore': get_linescore(data),
            'batting_stats': get_batting_stats(data),
            'pitching_stats': get_pitching_stats(data),
            'highlights': get_highlights(data)
        }
        return result
    else:
        logging.error(f"Error: Unable to fetch game data. Status code: {response.status_code}")
        logging.error(f"Response content: {response.text}")
        return None

def get_game_info(data):
    game_data = data['gameData']
    return {
        'game_pk': game_data['game']['pk'],
        'home_team': game_data['teams']['home']['name'],
        'away_team': game_data['teams']['away']['name'],
        'venue': game_data['venue']['name'],
        'date': datetime.strptime(game_data['datetime']['dateTime'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d"),
        'status': game_data['status']['detailedState'],
        'weather': game_data.get('weather', {}).get('condition', 'Not available'),
        'temp': game_data.get('weather', {}).get('temp', 'Not available'),
        'wind': game_data.get('weather', {}).get('wind', 'Not available')
    }

def get_linescore(data):
    linescore = data['liveData']['linescore']
    return {
        'home_score': linescore['teams']['home'].get('runs', 'N/A'),
        'away_score': linescore['teams']['away'].get('runs', 'N/A'),
        'inning': f"{linescore.get('currentInningOrdinal', 'N/A')} {linescore.get('inningState', '')}".strip(),
    }

def get_batting_stats(data):
    batting_stats = {}
    for team in ['away', 'home']:
        batting_stats[team] = []
        for player in data['liveData']['boxscore']['teams'][team]['batters']:
            player_data = data['liveData']['boxscore']['teams'][team]['players'][f'ID{player}']
            stats = player_data['stats']['batting']
            batting_stats[team].append({
                'name': player_data['person']['fullName'],
                'position': player_data['position']['abbreviation'],
                'ab': stats.get('atBats', 0),
                'r': stats.get('runs', 0),
                'h': stats.get('hits', 0),
                'rbi': stats.get('rbi', 0),
                'bb': stats.get('baseOnBalls', 0),
                'so': stats.get('strikeOuts', 0),
                'avg': stats.get('avg', '.000'),
                'ops': stats.get('ops', '.000')
            })
    return batting_stats

def get_pitching_stats(data):
    pitching_stats = {}
    for team in ['away', 'home']:
        pitching_stats[team] = []
        for player in data['liveData']['boxscore']['teams'][team]['pitchers']:
            player_data = data['liveData']['boxscore']['teams'][team]['players'][f'ID{player}']
            stats = player_data['stats']['pitching']
            pitching_stats[team].append({
                'name': player_data['person']['fullName'],
                'ip': stats.get('inningsPitched', '0.0'),
                'h': stats.get('hits', 0),
                'r': stats.get('runs', 0),
                'er': stats.get('earnedRuns', 0),
                'bb': stats.get('baseOnBalls', 0),
                'so': stats.get('strikeOuts', 0),
                'hr': stats.get('homeRuns', 0),
                'era': stats.get('era', '0.00')
            })
    return pitching_stats

def get_highlights(data):
    highlights = []
    for highlight in data.get('highlights', {}).get('highlights', {}).get('items', []):
        highlights.append({
            'title': highlight['headline'],
            'description': highlight['description'],
            'duration': highlight['duration'],
            'video_url': next((p['url'] for p in highlight['playbacks'] if p['name'] == 'mp4Avc'), None)
        })
    return highlights

def get_all_games_data():
    logging.info("Fetching all games data")
    date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    schedule = get_schedule(date)
    if schedule:
        if 'dates' in schedule and len(schedule['dates']) > 0:
            games = schedule['dates'][0]['games']
            if games:
                game = games[0]
                game_pk = game['gamePk']
                game_data = get_detailed_game_data(game_pk)
                if game_data:
                    home_team = game_data['game_info']['home_team']
                    away_team = game_data['game_info']['away_team']
                    logging.info(f"Fetched data for game {game_pk} ({away_team} at {home_team})")
                    return game_data
                else:
                    logging.info("No game data to process")
            else:
                logging.info(f"No games scheduled for {date}")
        else:
            logging.info(f"No games scheduled for {date}")
    else:
        logging.error("Failed to retrieve schedule")
    return None

def create_batting_chart(game_data):
    try:
        away_team = game_data['game_info']['away_team']
        home_team = game_data['game_info']['home_team']
        away_batters = game_data['batting_stats']['away']
        home_batters = game_data['batting_stats']['home']
        away_top5 = sorted(away_batters, key=lambda x: x['h'], reverse=True)[:5]
        home_top5 = sorted(home_batters, key=lambda x: x['h'], reverse=True)[:5]
        players = [player['name'] for player in away_top5 + home_top5]
        hits = [player['h'] for player in away_top5 + home_top5]
        rbis = [player['rbi'] for player in away_top5 + home_top5]

        plt.figure(figsize=(12, 6))
        x = range(len(players))
        plt.bar([i - 0.2 for i in x], hits, 0.4, label='Hits')
        plt.bar([i + 0.2 for i in x], rbis, 0.4, label='RBIs')
        plt.ylabel('Count')
        plt.title(f'Top 5 Batters: {away_team} vs {home_team}')
        plt.xticks(x, players, rotation=45, ha='right')
        plt.legend()
        plt.axvline(x=4.5, color='red', linestyle='--')
        plt.tight_layout()

        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, 'static/images/batting_chart.png')
        plt.savefig(file_path)
        plt.close()
        logging.info(f"Chart saved as '{file_path}'")

    except Exception as e:
        logging.error(f"Error in create_batting_chart: {e}")
        import traceback
        traceback.print_exc()

def generate_article_with_llm(game_data):
    logging.info(f"Generating article for game on {game_data['game_info']['date']}")
    # Initialize the GPT-Neo generator with a smaller model
    generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', device=-1)

    # Create a detailed prompt for the LLM
    prompt = f"Write a detailed sports news article about the baseball game between {game_data['game_info']['away_team']} and {game_data['game_info']['home_team']} on {game_data['game_info']['date']}. "
    prompt += f"The final score was {game_data['linescore']['away_score']} to {game_data['linescore']['home_score']}. "
    prompt += f"Highlights of the game include:\n"
    for highlight in game_data['highlights']:
        prompt += f"- {highlight['title']} ({highlight['description']})\n"

    logging.info("Prompt created, starting generation")
    # Generate the article using the model
    generated_text = generator(prompt, max_length=800, num_return_sequences=1, truncation=True)[0]['generated_text']
    logging.info("Article generated successfully")

    # Return the generated article
    return generated_text

if __name__ == "__main__":
    logging.info("Script started")
    game_data = get_all_games_data()
    if game_data:
        article = generate_article_with_llm(game_data)
        print(article)  # Print to console
        # Save the article to a file
        file_name = f"{game_data['game_info']['date']}_{game_data['game_info']['away_team']}_at_{game_data['game_info']['home_team']}.txt"
        with open(file_name, 'w') as file:
            file.write(article)
        logging.info(f"Article saved as {file_name}")
    else:
        logging.info("No game data to process")
    logging.info("Script completed")
