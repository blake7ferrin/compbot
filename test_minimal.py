"""Minimal Flask test to verify Flask works."""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def test():
    return 'WORKING - Flask is running!'

if __name__ == '__main__':
    print('=' * 60)
    print('MINIMAL FLASK TEST')
    print('=' * 60)
    print('Starting Flask on http://127.0.0.1:8888')
    print('If you see "Running on..." below, Flask is working!')
    print('Open http://127.0.0.1:8888 in your browser')
    print('=' * 60)
    app.run(host='127.0.0.1', port=8888, debug=True, use_reloader=False)

