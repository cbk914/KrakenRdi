import json
import os
import logging
import jsonschema
from flask import jsonify, request, abort, make_response
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.server.krakenServer import KrakenServer
from core.krakenrdi.api.common.validations import validateApiRequest, setDefaultsBuild

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BuildView:

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/list', methods=["GET", "POST"])
    def listBuilds():
        try:
            response = KrakenServer.buildService.list()
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error listing builds: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/create', methods=["PUT", "POST"])
    def createBuild():
        try:
            if KrakenConfiguration.taskEngine.control.inspect().active() is None:
                response = {"message": "Celery worker is down. Start the KrakenRDI worker using '-w' option"}
                return jsonify(response), 503
            if validateApiRequest(request, abort, schema="createBuild"):
                structure = setDefaultsBuild(request.json)
                response = KrakenServer.buildService.build(structure)
                return jsonify(response), 201
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error creating build: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/detail', methods=["POST"])
    def detailBuild():
        try:
            if validateApiRequest(request, abort, schema="detailBuild"):
                structure = setDefaultsBuild(request.json)
                response = KrakenServer.buildService.detail(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error getting build details: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/delete', methods=["POST", "DELETE"])
    def deleteBuild():
        try:
            if validateApiRequest(request, abort, schema="deleteBuild"):
                structure = setDefaultsBuild(request.json)
                response = KrakenServer.buildService.delete(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error deleting build: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/filter', methods=["POST"])
    def filterBuild():
        try:
            # Assuming filter functionality is not implemented yet
            build = {}
            return jsonify(build), 200
        except Exception as e:
            logger.error(f"Error filtering builds: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/build/status', methods=["POST"])
    def statusBuild():
        try:
            # Assuming status check functionality is not implemented yet
            build = {}
            return jsonify(build), 200
        except Exception as e:
            logger.error(f"Error checking build status: {e}")
            return jsonify({'message': 'Internal server error'}), 500
