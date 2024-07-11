import os
from flask import Flask, render_template, url_for
from your_existing_script import get_all_games_data, create_batting_chart

app = Flask(__name__)

@app.route('/')
def index():
    date = "2024-07-10"  # Example date, you might want to make this dynamic
    all_games_data = get_all_games_data(date)
    return render_template('index.html', games=all_games_data)

@app.route('/game/<int:game_pk>')
def game_detail(game_pk):
    all_games_data = get_all_games_data("2024-07-10")
    game_data = next((game for game in all_games_data if game['game_info']['game_pk'] == game_pk), None)
    if game_data:
        create_batting_chart(game_data)
    return render_template('game_detail.html', game=game_data)

if __name__ == "__main__":
    app.run(debug=True)
