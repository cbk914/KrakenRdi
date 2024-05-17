import json
import logging
import secrets
from jsonpickle import encode
from docker.errors import ImageNotFound
from core.krakenrdi.backend.asyncro.tasks import createBuild
from core.krakenrdi.backend.connector.entities import Image, Container, Tool
from core.krakenrdi.backend.connector.builder import DockerManagerConnection
from core.krakenrdi.api.common.validations import BusinessValidations

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KrakenManager:

    def __init__(self, database, configuration):
        self.database = database
        self.configuration = configuration
        self.buildService = None
        self.containerService = None
        self.toolService = None
        self.dockerManager = DockerManagerConnection()
        self.businessValidations = BusinessValidations(self.dockerManager)

    def getBuildService(self):
        if self.buildService is None:
            self.buildService = BuildService(self)
        return self.buildService

    def getContainerService(self):
        if self.containerService is None:
            self.containerService = ContainerService(self)
        return self.containerService

    def getToolService(self):
        if self.toolService is None:
            self.toolService = ToolService(self)
        return self.toolService

class BuildService:

    def __init__(self, manager):
        self.manager = manager

    def __getBuilds(self, buildsStored):
        response = []
        for build in buildsStored:
            shortName = build['buildName'].split(':')[1] if ':' in build['buildName'] else build['buildName']
            response.append({
                'buildFullName': build['buildName'],
                'buildName': shortName,
                'buildScope': build['buildScope'],
                'tools': build['tools'],
                'containerProperties': build['buildArgs'],
                'startSSH': build['startSSH'],
                'startPostgres': build['startPostgres'],
                'taskState': build['taskState'],
                'memoryLimit': build['memoryLimit']
            })
        return response

    def build(self, request):
        result = {}
        buildName = f"{self.manager.configuration['config']['imageBase']}:{request['buildName']}"
        buildFound = self.manager.database.builds.find({'buildName': buildName})
        numberBuilds = len(list(buildFound))

        if numberBuilds > 0 and not request.get("overwrite", False):
            return {"message": "The name of the image already used. Choose another one or if you want to overwrite that image, send 'overwrite' parameter in the JSON structure."}

        toolsEnabled = self.manager.database.tools.find({'name': {'$in': request['tools']}})
        toolsDisabled = self.manager.database.tools.find({'name': {'$nin': request['tools']}})

        imageCreate = self._prepare_image_create(request, toolsEnabled, toolsDisabled)

        if numberBuilds > 0 and request.get("overwrite", False):
            self.manager.database.builds.delete_one({'buildName': buildName})

        result = json.loads(encode(imageCreate).replace("\\", ""))
        result.pop("py/object", None)
        result.update({
            "tools": request['tools'],
            "taskId": f"{imageCreate.buildName}-{secrets.token_hex(8)}",
            "taskState": "CREATED"
        })

        self.manager.database.builds.insert_one(result)
        createBuild.apply_async((encode(imageCreate),), task_id=result["taskId"])

        del result["_id"]
        return result

    def _prepare_image_create(self, request, toolsEnabled, toolsDisabled):
        imageCreate = Image()
        imageCreate.buildName = f"{self.manager.configuration['config']['imageBase']}:{request['buildName']}"
        imageCreate.buildScope = request['buildScope']
        imageCreate.startSSH = request['startSSH']
        imageCreate.startPostgres = request['startPostgres']

        for tool in toolsEnabled:
            if 'propertyEnabled' in tool:
                imageCreate.buildArgs[tool['propertyEnabled']] = 'True'

        for tool in toolsDisabled:
            if 'propertyEnabled' in tool:
                imageCreate.buildArgs[tool['propertyEnabled']] = 'False'

        if "containerProperties" in request:
            for containerProperty, value in request['containerProperties'].items():
                imageCreate.buildArgs[containerProperty] = ' '.join(map(str, value)) if "EXPOSE_PORTS" in containerProperty else value

        return imageCreate

    def list(self):
        buildsStored = self.manager.database.builds.find({})
        return self.__getBuilds(buildsStored)

    def detail(self, request):
        buildsStored = self.manager.database.builds.find({'buildName': f"{self.manager.configuration['config']['imageBase']}:{request['buildName']}"})
        return self.__getBuilds(buildsStored)

    def delete(self, request):
        buildName = f"{self.manager.configuration['config']['imageBase']}:{request['buildName']}"
        result = {}
        try:
            result = self.manager.dockerManager.imageBuilder.delete(buildName)
        except ImageNotFound:
            logger.warning(f"Image not found in Docker service: {buildName}")
            return {"message": "Image not found in Docker service. If it existed in database it was already deleted too"}
        finally:
            self.manager.database.builds.delete_one({'buildName': buildName})
            return result

class ContainerService:
    def __init__(self, manager):
        self.manager = manager

    def list(self):
        containers = self.manager.database.containers.find()
        result = []
        for container in containers:
            container_info = {
                "buildName": container["buildName"],
                "containerName": container["containerName"],
                "containerPorts": container["ports"],
                "containerVolumes": container["volumes"],
                "containerStatus": self.manager.dockerManager.containerBuilder.checkStatus(container["containerName"])
            }
            result.append(container_info)
        return result

    def get(self, request):
        containerFound = self.manager.database.containers.find_one({"containerName": request["containerName"]})
        if containerFound:
            del containerFound["_id"]
            return containerFound
        return {"message": "Container not found in database."}

    def create(self, request):
        result = {}
        buildName = f"{self.manager.configuration['config']['imageBase']}:{request['buildName']}"

        if not self._is_build_available(buildName):
            return {"message": f"The specified image {request['buildName']} doesn't exist"}

        stateBuild = self._get_ready_build_state(buildName)
        if not stateBuild:
            return {"message": f"The image {request['buildName']} is not ready yet. The image is still in the creation process."}

        request['buildName'] = buildName
        containerStructure = self.manager.businessValidations.validateContainerStructure(request)
        if not containerStructure["valid"]:
            return containerStructure

        container = self._prepare_container(containerStructure)

        dockerContainer = self.manager.dockerManager.containerBuilder.create(container)

        self._start_services(dockerContainer, stateBuild)

        result = self._register_container(dockerContainer, container)
        return result

    def _is_build_available(self, buildName):
        build = self.manager.database.builds.find({'buildName': buildName})
        return len(list(build)) > 0

    def _get_ready_build_state(self, buildName):
        return self.manager.database.builds.find_one({'taskState': {'$in': ["READY", "SAVED", "FINISHED"]}})

    def _prepare_container(self, containerStructure):
        container = Container()
        container.buildName = containerStructure["buildName"]
        container.containerName = containerStructure["containerName"]
        container.capAdd = containerStructure["capAdd"]
        container.capDrop = containerStructure["capDrop"]
        container.hostname = containerStructure["hostname"]
        container.memoryLimit = containerStructure["memoryLimit"]
        container.networkMode = containerStructure["networkMode"]
        container.networkDisabled = containerStructure["networkDisabled"]
        container.readOnly = containerStructure["readOnly"]
        container.ports = containerStructure["ports"]
        container.volumes = containerStructure["volumes"]
        container.environment = containerStructure["environment"]
        return container

    def _start_services(self, dockerContainer, stateBuild):
        if stateBuild["startSSH"]:
            dockerContainer.exec_run("/etc/init.d/ssh start", user="root")
            dockerContainer.exec_run(f"export DISPLAY={os.environ['DISPLAY']}")
            dockerContainer.startSSH = True
        if stateBuild["startPostgres"]:
            dockerContainer.exec_run("/etc/init.d/postgresql start", user="root")
            dockerContainer.startPostgres = True

    def _register_container(self, dockerContainer, container):
        result = {
            "containerId": dockerContainer.id,
            "containerImage": dockerContainer.attrs,
            "containerName": dockerContainer.name,
            "containerStatus": dockerContainer.status
        }

        self.manager.database.containers.delete_one({'containerName': dockerContainer.name})
        containerJson = json.loads(encode(container).replace("\\", "").replace(".", ""))
        containerJson.pop("py/object", None)
        self.manager.database.containers.insert_one(containerJson)
        return result

    def delete(self, request):
        containerName = request["containerName"]
        self.manager.database.containers.delete_one({"containerName": containerName})
        success = self.manager.dockerManager.containerBuilder.delete(containerName)

        if success:
            return {"message": "Container removed from database and Docker engine."}
        else:
            return {"message": "Failed to remove container from Docker engine or database."}

    def stop(self, request):
        containerName = request["containerName"]
        self.manager.database.containers.update_one({"containerName": containerName}, {"$set": {"status": "stopped"}})
        success = self.manager.dockerManager.containerBuilder.stop(containerName)

        if success:
            return {"message": "Container stopped successfully."}
        else:
            return {"message": "Failed to stop container."}

class ToolService:
    def __init__(self, manager):
        self.manager = manager

    def __getTools(self, toolsStored):
        response = []
        for tool in toolsStored:
            response.append({
                'toolName': tool['name'],
                'toolDescription': tool['description'],
                'toolURL': tool['url'],
                'toolScope': {"RT": tool['RT'], "PT": tool['PT']}
            })
        return response

    def list(self):
        toolsStored = self.manager.database.tools.find({})
        return self.__getTools(toolsStored)

    def filter(self, request):
        toolsStored = self.manager.database.tools.find({'name': {'$regex': request['toolName'], "$options": "-i"}})
        return self.__getTools(toolsStored)

    def info(self, request):
        tool = self.manager.database.tools.find_one({"name": request["toolName"]})
        if tool:
            return {
                'toolName': tool['name'],
                'toolDescription': tool['description'],
                'toolURL': tool['url'],
                'toolScope': {"RT": tool['RT'], "PT": tool['PT']}
            }
        return {"message": "Tool not found"}
