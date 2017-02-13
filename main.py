from app import flaskapp
import os

if __name__ == '__main__':
    # app.config.from_object('application.settings')
    # print 'ivan', app.config['hello']
    flaskapp.run(host='0.0.0.0', debug=not os.environ.get('HEROKU'))
