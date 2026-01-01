from flask import Flask

test_app = Flask(__name__)

@test_app.route('/')
def home():
    return "Server is working! ✅"

if __name__ == '__main__':
    print("Starting test server on http://localhost:5000")
    test_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
