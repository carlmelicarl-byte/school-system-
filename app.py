#!/usr/bin/env python3
import os

from school_system import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
