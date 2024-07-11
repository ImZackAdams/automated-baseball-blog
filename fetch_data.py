import os
import random
import requests
import time
import logging
from datetime import datetime, timedelta
from transformers import pipeline

# Set environment variable to handle unsupported operations on MPS if using Apple Silicon Mac
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

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
        return {
            'game_info': get_game_info(data),
            'linescore': get_linescore(data),
            'batting_stats': get_batting_stats(data),
            'pitching_stats': get_pitching_stats(data),
            'highlights': get_highlights(data)
        }
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

from transformers import pipeline
import logging

import torch
from transformers import pipeline
import logging

def generate_narrative_style_article(game_data):
    logging.info(f"Generating narrative-style article for game on {game_data['game_info']['date']}")

    # Initialize the GPT-Neo model pipeline
    device = -1  # Assuming CPU usage
    generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', device=device)

    # Construct a detailed prompt with unique player statistics
    prompt = f"The game at {game_data['game_info']['venue']} on {game_data['game_info']['date']} featured a thrilling match between {game_data['game_info']['home_team']} and {game_data['game_info']['away_team']}. Here are some highlights and key performances:"

    player_contributions = {}
    for team in ['home', 'away']:
        for player_stats in game_data['batting_stats'][team]:
            player_key = player_stats['name']
            if player_key not in player_contributions or player_stats['h'] > player_contributions[player_key][1]:  # Only add if this is a better performance or not added yet
                player_contributions[player_key] = (f"{player_stats['name']} with {player_stats['h']} hits and {player_stats['rbi']} RBIs", player_stats['h'])

    for contribution, _ in player_contributions.values():
        prompt += f"\n- {contribution}"

    logging.debug("Final prompt to model: " + prompt)

    # Generate the narrative
    generated_text = generator(prompt, max_length=500, num_return_sequences=1, no_repeat_ngram_size=2, truncation=True)[0]['generated_text']
    logging.info("Narrative article generated successfully")

    return generated_text
# Example usage
if __name__ == "__main__":
    logging.info("Script started")
    game_data = get_all_games_data()
    if game_data:
        narrative_article = generate_narrative_style_article(game_data)
        print(narrative_article)
    logging.info("Script completed")
