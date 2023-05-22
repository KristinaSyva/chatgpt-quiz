### Activation

- source venv/bin/activate

- export FLASK_APP=app

- export FLASK_ENV=development

- export DATABASE_URL=...

- nodemon --exec "flask run"

- flask run

### Alternative option:

Add this parameters in .flaskenv file
- nodemon --exec "flask run"
- flask run

### Some commands for database table create and drop

For database table create

- flask create_db

For database table drop

- flask delete_db
