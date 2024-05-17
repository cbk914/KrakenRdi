import logging
import json
import os
import jsonschema
from flask import jsonify, request, abort, make_response
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.server.krakenServer import KrakenServer
from core.krakenrdi.api.common.validations import validateApiRequest, setDefaultsTool
from jsonpickle import encode

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ToolView:

    @staticmethod
    @KrakenConfiguration.restApi.route('/tools/stages', methods=["GET", "POST"])
    def stagesTools():
        try:
            response = {"toolStages": ["common", "framework", "candc", "delivery",
                                       "escalation", "exfiltration", "exploitation",
                                       "internalrecon", "movelateral", "recon", "weapon", "all"]}
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error retrieving tool stages: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/tools/list', methods=["GET", "POST"])
    def listTools():
        try:
            response = KrakenServer.toolService.list()
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/tools/info', methods=["POST"])
    def infoTools():
        try:
            if validateApiRequest(request, abort, schema="infoToolSchema"):
                structure = setDefaultsTool(request.json)
                response = KrakenServer.toolService.info(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error getting tool info: {e}")
            return jsonify({'message': 'Internal server error'}), 500

    @staticmethod
    @KrakenConfiguration.restApi.route('/tools/filter', methods=["POST"])
    def filterTools():
        try:
            if validateApiRequest(request, abort, schema="filterToolSchema"):
                structure = setDefaultsTool(request.json)
                response = KrakenServer.toolService.filter(structure)
                return jsonify(response), 200
            return jsonify({'message': 'Invalid request'}), 400
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'message': 'Invalid request schema'}), 400
        except Exception as e:
            logger.error(f"Error filtering tools: {e}")
            return jsonify({'message': 'Internal server error'}), 500
