### Project

This is a Python Flask web application. It allows users to generate a quiz with the help of Chat GPT API, add it to database, play the quiz, make the quiz public to other users and see the scoreboard of each score after finishing the game.

### Activation

Make sure to create a .env file based on the format of .env.example and populate it with your own parameters.

# Activate the virtual environment:

- source venv/bin/activate

# Set the Flask app and environment variables:

- export FLASK_APP=app

- export FLASK_ENV=development

- export DATABASE_URL=...

# Run the application using nodemon (automatically restarts on file changes):

- nodemon --exec "flask run"

OR

# Run the application using Flask:

- flask run
