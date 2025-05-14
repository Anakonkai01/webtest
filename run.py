# Anakonkai01/webtest/webtest-56020c9fc852ddd6495dc0e46baf7ebb8913bd4a/run.py
import os
from app import create_app

config_name = os.getenv('FLASK_ENV', 'dev') 

app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 