from flask_migrate import Migrate

from extds import db
from apps import create_app

import model

app = create_app()
migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run()