import os
import sys
import logging
from flask import Flask, jsonify, abort, make_response, request
from flask_pymongo import PyMongo
from celery import Celery, shared_task
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.backend.ServiceManager import KrakenManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KrakenServer:
    
    buildService = None
    containerService = None
    toolService = None

    @staticmethod
    def configureServices():
        coreManager = KrakenManager(
            database=KrakenConfiguration.database,
            configuration=KrakenConfiguration.configuration
        )
        KrakenServer.buildService = coreManager.getBuildService()
        KrakenServer.containerService = coreManager.getContainerService()
        KrakenServer.toolService = coreManager.getToolService()

    @staticmethod
    def init(configuration, tools, arguments, cleanDB):
        KrakenConfiguration.configuration = configuration
        KrakenConfiguration.restApi.config['DEBUG'] = True
        # Database initialization
        KrakenConfiguration.restApi.config['MONGO_DBNAME'] = os.getenv('DATABASE_NAME', configuration['config']['databaseName'])
        KrakenConfiguration.restApi.config['MONGO_URI'] = os.getenv('DATABASE_URI', configuration['config']['databaseURI'])
        # Celery configuration
        KrakenConfiguration.restApi.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', configuration['config']['celeryBrokerUrl'])
        KrakenConfiguration.restApi.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', configuration['config']['celeryResultBackend'])
        KrakenConfiguration.restApi.config['CELERY_TRACK_STARTED'] = True
        KrakenConfiguration.restApi.config['CELERY_SEND_EVENTS'] = True
        KrakenConfiguration.taskEngine.conf.update(KrakenConfiguration.restApi.config)

        try:
            # Connect with MongoDB
            dbConnection = PyMongo(KrakenConfiguration.restApi)
            KrakenConfiguration.database = dbConnection.db
            if cleanDB:
                for collectionDB in KrakenConfiguration.database.list_collection_names():
                    KrakenConfiguration.database.drop_collection(collectionDB)
            if "arguments" not in KrakenConfiguration.database.list_collection_names():
                KrakenConfiguration.database.arguments.insert_many(arguments)
            if "tools" not in KrakenConfiguration.database.list_collection_names():
                KrakenConfiguration.database.tools.insert_many(tools)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            logger.error(f"Check that your Mongo server is running at {KrakenConfiguration.restApi.config['MONGO_URI']}")
            sys.exit(1)

    @KrakenConfiguration.restApi.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return make_response(jsonify({'message': 'Internal server error occurred'}), 500)

    @KrakenConfiguration.restApi.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {error}")
        return make_response(jsonify({'message': 'Bad request'}), 400)

    @KrakenConfiguration.restApi.errorhandler(404)
    def not_found_request(error):
        logger.info(f"Resource not found: {error}")
        return make_response(jsonify({'message': 'Resource not found'}), 404)
