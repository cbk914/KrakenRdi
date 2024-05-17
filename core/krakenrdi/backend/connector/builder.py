import logging
import docker
from jsonpickle import decode
import json
from docker.errors import NotFound
from core.krakenrdi.server.CoreObjects import KrakenConfiguration

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DockerManagerConnection:
    def __init__(self, dockerUrl=None):
        self.dockerClient = self._connect_to_docker(dockerUrl)
        if self.dockerClient:
            self.imageBuilder = ImageBuilder(self.dockerClient.images, self.dockerClient.containers)
            self.containerBuilder = ContainerBuilder(self.dockerClient.containers)

    def _connect_to_docker(self, dockerUrl):
        try:
            if dockerUrl is None:
                client = docker.from_env()
            else:
                client = docker.DockerClient(base_url=dockerUrl)
            
            if client.ping():
                return client
            else:
                logger.error("Failed to ping Docker daemon")
                return None
        except docker.errors.DockerException as e:
            logger.error(f"Error connecting to Docker daemon: {e}")
            return None

class ImageBuilder:
    def __init__(self, imageDockerObject, containerDockerObject):
        self.imageDockerObject = imageDockerObject
        self.containerDockerObject = containerDockerObject

    def build(self, image):
        try:
            imageObj = decode(image)
            path = os.path.join(os.getcwd(), KrakenConfiguration.configuration['config']['pathDockerImages'])
            tag = imageObj.buildName
            buildArgs = imageObj.buildArgs
            dockerfile = KrakenConfiguration.configuration['config']['dockerImages']['BASE']

            imageBuilded, buildLogs = self.imageDockerObject.build(
                path=path,
                dockerfile=dockerfile,
                buildargs=buildArgs,
                tag=tag,
                shmsize="536870912",
                quiet=False,
                rm=True,
                forcerm=True
            )

            logger.info("Image built successfully.")
            self.imageDockerObject.prune(filters={"dangling": True})
            logs = self._parse_build_logs(buildLogs)
            return json.dumps({"imageId": imageBuilded.id, "imageLabels": imageBuilded.labels, "imageTags": imageBuilded.tags, "imageLogs": logs})
        
        except docker.errors.BuildError as e:
            logger.error(f"Error building Docker image: {e}")
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return json.dumps({"error": str(e)})

    def _parse_build_logs(self, buildLogs):
        logs = []
        for log in buildLogs:
            for dictValue in log.values():
                if dictValue:
                    logs.append(str(dictValue))
        return logs

    def delete(self, imageName):
        try:
            containersRunning = self.containerDockerObject.list(filters={"ancestor": imageName})
            for container in containersRunning:
                container.stop()
                container.remove()
            self.imageDockerObject.remove(image=imageName, force=True, noprune=False)
            logger.info(f"Image {imageName} deleted successfully.")
            return {"message": "Image deleted from database and docker service."}
        except NotFound:
            logger.warning(f"Image {imageName} not found.")
            return {"message": "Image not found in Docker service."}
        except docker.errors.APIError as e:
            logger.error(f"Error removing image {imageName}: {e}")
            return {"message": f"Error removing image: {e}"}

class ContainerBuilder:
    def __init__(self, containerDockerObject):
        self.containerDockerObject = containerDockerObject

    def create(self, container):
        try:
            dockerContainer = self.containerDockerObject.run(
                image=container.buildName,
                auto_remove=container.autoRemove,
                cap_add=container.capAdd,
                cap_drop=container.capDrop,
                detach=True,
                mem_limit=container.memoryLimit,
                name=container.containerName,
                network_mode=container.networkMode,
                ports=container.ports,
                read_only=container.readOnly,
                tty=container.tty,
                volumes=container.volumes,
                privileged=container.privileged,
                environment=container.environment
            )
            logger.info(f"Container {container.containerName} created successfully.")
            return dockerContainer
        except docker.errors.ContainerError as e:
            logger.error(f"Error creating container {container.containerName}: {e}")
            return {"message": f"Error creating container: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"message": f"Unexpected error: {e}"}

    def checkStatus(self, containerName):
        try:
            container = self.containerDockerObject.get(containerName)
            return container.status if container else "NOT_FOUND"
        except NotFound:
            return "NOT_FOUND"
        except Exception as e:
            logger.error(f"Error checking status of container {containerName}: {e}")
            return "ERROR"

    def stop(self, containerName):
        try:
            container = self.containerDockerObject.get(containerName)
            container.stop()
            logger.info(f"Container {containerName} stopped successfully.")
            return container.status
        except NotFound:
            return "NOT_FOUND"
        except docker.errors.APIError as e:
            logger.error(f"Error stopping container {containerName}: {e}")
            return "ERROR_STOPPING"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "ERROR_GETTING_CONTAINER"

    def delete(self, containerName):
        try:
            self.containerDockerObject.remove(containerName, force=True)
            logger.info(f"Container {containerName} deleted successfully.")
            return True
        except NotFound:
            logger.warning(f"Container {containerName} not found.")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Error deleting container {containerName}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
