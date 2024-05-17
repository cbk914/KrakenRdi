from flask import Flask
from celery import Celery
import logging

class KrakenConfiguration():
	restApi = Flask(__name__)
	#
	# Initialize Celery
	taskEngine = Celery(restApi.name, 
						backend='redis://localhost:6379/0', 
						broker='redis://localhost:6379/0',
						include=['core.krakenrdi.backend.asyncro.tasks'])
	taskEngine.conf.update(restApi.config)
	database = None
	configuration = {}
	logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)

import os
import logging
from flask import Flask
from celery import Celery

class KrakenConfiguration:
    restApi = Flask(__name__)

    # Setup logging
    logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    try:
        # Initialize Celery with configuration from environment variables
        redis_backend = os.getenv('REDIS_BACKEND', 'redis://localhost:6379/0')
        redis_broker = os.getenv('REDIS_BROKER', 'redis://localhost:6379/0')
        
        taskEngine = Celery(
            restApi.name,
            backend=redis_backend,
            broker=redis_broker,
            include=['core.krakenrdi.backend.asyncro.tasks']
        )
        taskEngine.conf.update(restApi.config)
        logger.info("Celery initialized successfully.")
        
    except Exception as e:
        logger.error(f"Failed to initialize Celery: {e}")
        raise

    database = None
    configuration = {}

