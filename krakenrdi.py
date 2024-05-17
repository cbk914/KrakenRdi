import json
import os
import sys
import logging
from plumbum import cli
from core.krakenrdi.api.build.view import BuildView
from core.krakenrdi.api.container.view import ContainerView
from core.krakenrdi.api.tool.view import ToolView
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.server.krakenServer import KrakenServer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(filepath):
    try:
        with open(filepath) as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from file: {filepath}")
    except Exception as e:
        logger.error(f"Unexpected error reading file {filepath}: {e}")
    sys.exit(1)

class KrakenRDI(cli.Application):
    restApiCli = cli.Flag(["-r", "--start-restapi"], help="Start Rest API.")
    workerCli = cli.Flag(["-w", "--start-worker"], help="Start Celery worker.")
    cleanDatabase = cli.Flag(["-c", "--clean-database"], help="Restore the database with default values and cleans the current data.", default=False)

    def main(self):
        if self.restApiCli or self.workerCli:
            logger.info("Initialization tasks...")
            self.configuration = load_json_file('config/config.json')
            self.tools = load_json_file('config/tools.json')
            self.arguments = load_json_file('config/arguments.json')

            KrakenServer.init(self.configuration, self.tools, self.arguments, self.cleanDatabase)
            logger.info("Configuration established.")
            KrakenServer.configureServices()
            logger.info("Core services for the Rest API configured.")
        
        if self.restApiCli:
            logger.info("Starting webserver and Rest API...")
            self.startRestApi()
        elif self.workerCli:
            logger.info("Starting Celery worker...")
            self.startWorker()

    def startRestApi(self):
        KrakenConfiguration.restApi.run()

    def startWorker(self):
        from celery import current_app
        from celery.bin import worker

        # Celery 5.x Worker Start
        worker = KrakenConfiguration.taskEngine.Worker(include=['core.krakenrdi.backend.asyncro.tasks'])
        worker.start()
        logger.info("Worker started successfully. Now, from another terminal, start the Rest API to complete the Kraken startup...")

if __name__ == '__main__':
    KrakenRDI.run()
