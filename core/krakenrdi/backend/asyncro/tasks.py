from __future__ import absolute_import
import time
import logging
import json
from celery import Celery, shared_task
from core.krakenrdi.server.CoreObjects import KrakenConfiguration
from core.krakenrdi.backend.connector.builder import DockerManagerConnection

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

@KrakenConfiguration.taskEngine.task(bind=True)
def createBuild(self, imageJson):
    try:
        buildStored = KrakenConfiguration.database.builds.find_one({"taskId": self.request.id})
        if not buildStored:
            raise ValueError(f"No build found with taskId: {self.request.id}")

        update_task_state(buildStored, 'PROCESSING', 'Calling Docker service to create image.')

        dockerManager = DockerManagerConnection()
        imageCreated = dockerManager.imageBuilder.build(imageJson)
        imageStore = json.loads(imageCreated)

        update_task_state(buildStored, 'READY', 'Image created successfully and ready to create containers.')

        imageStore["taskId"] = self.request.id
        KrakenConfiguration.database.builds_history.insert_one(imageStore)

        update_task_state(buildStored, 'SAVED', 'Image logs saved successfully in database.')

    except ValueError as ve:
        handle_exception(buildStored, f"Validation error: {ve}")
    except json.JSONDecodeError as je:
        handle_exception(buildStored, f"JSON decode error: {je}")
    except Exception as e:
        handle_exception(buildStored, f"Error during image creation: {e}")
    else:
        update_task_state(buildStored, 'FINISHED', 'Task finished.')

def update_task_state(buildStored, status, message):
    buildStored["taskState"] = {'status': status, 'message': message}
    KrakenConfiguration.database.builds.update_one({'_id': buildStored["_id"]}, {"$set": buildStored}, upsert=False)
    logger.info(f"Updated task state to {status}: {message}")

def handle_exception(buildStored, message):
    update_task_state(buildStored, 'ERROR', message)
    logger.error(message)
