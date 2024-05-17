import logging
import json
import os
import jsonschema
from flask import jsonify, request, abort, make_response
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.server.krakenServer import KrakenServer
from core.krakenrdi.api.common.validations import validateApiRequest, setDefaultsContainer
from jsonpickle import encode

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ContainerView:

    @staticmethod
    @KrakenConfiguration.restApi.route('/container/list', methods=["GET", "POST"])
    def listContainers():
        try:
            response = KrakenServer.containerService.list()
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/container/get', methods=["POST"])
    def getContainer():
        try:
            if validateApiRequest(request, abort, schema="getContainer"):
                structure = setDefaultsContainer(request.json)
                response = KrakenServer.containerService.get(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error getting container: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/container/create', methods=["PUT", "POST"])
    def createContainer():
        try:
            if validateApiRequest(request, abort, schema="createContainer"):
                structure = setDefaultsContainer(request.json)
                response = KrakenServer.containerService.create(structure)
                return jsonify(response), 201
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/container/delete', methods=["PUT", "POST"])
    def deleteContainer():
        try:
            if validateApiRequest(request, abort, schema="deleteContainer"):
                structure = setDefaultsContainer(request.json)
                response = KrakenServer.containerService.delete(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error deleting container: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/container/stop', methods=["PUT", "POST"])
    def stopContainer():
        try:
            if validateApiRequest(request, abort, schema="stopContainer"):
                structure = setDefaultsContainer(request.json)
                response = KrakenServer.containerService.stop(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return jsonify({'message': 'Internal server error'}), 500
