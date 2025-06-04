# Study Site

This project is a Django based web application that includes several apps such as quizzes, trophies, attendance tracking and more.

## Setup

1. Create and activate a Python virtual environment.

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies. The project requires Django, PostgreSQL drivers,
   Pillow for image handling and PyMuPDF for PDF processing.

```bash
pip install -r requirements.txt
```

Channels and WebSockets support have been removed from the default setup,
so no additional asynchronous libraries are required.

3. Apply migrations and run the development server.

```bash
python manage.py migrate
python manage.py runserver
```

The project uses PostgreSQL by default. Update the database settings in `study_site/settings.py` if necessary.

## Static Assets

Game-related JavaScript files now live under `minigame/static/js/games/`. Each
game has a folder containing `single.js`, `multi.js` and `config.json`. Common
utilities are provided in `js/games/common/`.
