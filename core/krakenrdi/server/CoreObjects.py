from flask import Flask
from celery import Celery


class KrakenConfiguration():
	restApi = Flask(__name__)
	#
	# Initialize Celery
	taskEngine = Celery(restApi.name, 
						backend='redis://localhost:6379/0', 
						broker='redis://localhost:6379/0',
						include=['core.krakenrdi.backend.async.tasks'])
	taskEngine.conf.update(restApi.config)
	database = None
	configuration = {}
