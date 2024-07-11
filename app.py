from flask import Flask, render_template
from fetch_data import get_all_games_data, create_batting_chart
from datetime import datetime, timedelta
app = Flask(__name__)

@app.route('/')
def index():
    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Automatically set to yesterday's date
    all_games_data = get_all_games_data()
    return render_template('index.html', games=all_games_data)

@app.route('/game/<int:game_pk>')
def game_detail(game_pk):
    date = "2024-07-10"  # Example date, you might want to make this dynamic
    all_games_data = get_all_games_data(date)
    game_data = next((game for game in all_games_data if game['game_info']['game_pk'] == game_pk), None)
    if game_data:
        create_batting_chart(game_data)
    return render_template('game_detail.html', game=game_data)

if __name__ == "__main__":
    app.run(debug=True)
