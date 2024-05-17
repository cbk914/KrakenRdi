import json
import re
import logging
from os import environ
from jsonschema import validate, ValidationError
from core.krakenrdi.api.common.schemas import (
    createBuildSchema, deleteBuildSchema, detailBuildSchema, createContainerSchema,
    deleteContainerSchema, stopContainerSchema, getContainerSchema, infoToolSchema, filterToolSchema
)
from core.krakenrdi.api.common.schemas import defaultsBuild, defaultsContainer, defaultsTool

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def __setDefaults(jsonRequest, typeStructure):
    for attribute in typeStructure.keys():
        if attribute not in jsonRequest.keys():
            jsonRequest[attribute] = typeStructure[attribute]
    return jsonRequest

def setDefaultsBuild(request):
    return __setDefaults(request, defaultsBuild)

def setDefaultsContainer(request):
    return __setDefaults(request, defaultsContainer)

def setDefaultsTool(request):
    return __setDefaults(request, defaultsTool)

def validateApiRequest(request, abort, schema):
    schemas = {
        "createBuild": createBuildSchema,
        "detailBuild": detailBuildSchema,
        "deleteBuild": deleteBuildSchema,
        "createContainer": createContainerSchema,
        "deleteContainer": deleteContainerSchema,
        "stopContainer": stopContainerSchema,
        "getContainer": getContainerSchema,
        "infoToolSchema": infoToolSchema,
        "filterToolSchema": filterToolSchema
    }
    
    if not request.is_json:
        abort(400, "Invalid request: Content-Type must be application/json")
    if schema not in schemas:
        abort(400, "Invalid request: Unknown schema")
    
    try:
        validate(instance=request.json, schema=schemas[schema])
    except ValidationError as err:
        logger.warning(f"Validation error: {err}")
        abort(400, err.message)
    return True

class BusinessValidations:
    def __init__(self, dockerManager):
        self.dockerManager = dockerManager

    def validateBuildStructure(self):
        pass

    def validateContainerStructure(self, container):
        containerStructure = {
            "valid": False,
            "message": ""
        }
        
        if not self._validate_image_exists(container, containerStructure):
            return containerStructure
        
        if not self._validate_container_name(container, containerStructure):
            return containerStructure
        
        containerStructure.update({
            "buildName": container["buildName"],
            "containerName": container.get("containerName"),
            "volumes": self._validate_volumes(container),
            "ports": self._validate_ports(container),
            "environment": self._validate_environment(container),
            "memoryLimit": self._validate_memory_limit(container),
            "autoRemove": container.get("autoRemove"),
            "capAdd": container.get("capAdd"),
            "capDrop": container.get("capDrop"),
            "hostname": container.get("hostname"),
            "networkMode": container.get("networkMode"),
            "privileged": container.get("privileged"),
            "networkDisabled": container.get("networkDisabled"),
            "readOnly": container.get("readOnly"),
            "removeOnFinish": container.get("removeOnFinish"),
            "valid": True
        })
        
        return containerStructure

    def _validate_image_exists(self, container, containerStructure):
        try:
            self.dockerManager.imageBuilder.imageDockerObject.get(container["buildName"])
        except:
            containerStructure["message"] = "Image not found"
            return False
        return True

    def _validate_container_name(self, container, containerStructure):
        containerFound = None
        if "containerName" in container:
            try:
                containerFound = self.dockerManager.containerBuilder.containerDockerObject.get(container["containerName"])
            except:
                pass
            
            if containerFound:
                if "removeIfExists" in container and container["removeIfExists"]:
                    containerFound.stop(timeout=30)
                    containerFound.remove()
                else:
                    containerStructure["message"] = f"Container {container['containerName']} already exists. Choose another name or set 'removeIfExists' to True."
                    return False
        return True

    def _validate_volumes(self, container):
        volumes = {}
        if "volumes" in container:
            for volume in container["volumes"]:
                hostVolume = volume["hostVolume"]
                containerVolume = {"bind": volume["containerVolume"], "mode": volume["modeVolume"]}
                volumes[hostVolume] = containerVolume
        return volumes

    def _validate_ports(self, container):
        ports = {}
        if "ports" in container:
            for port in container["ports"]:
                portContainer = f"{port['portContainer']}/{port.get('protocolContainer', 'tcp')}"
                portHost = f"{port['portHost']}/{port.get('protocolHost', 'tcp')}" if "portHost" in port else None
                ports[portContainer] = portHost
        return ports

    def _validate_environment(self, container):
        environment = container.get("environment", [])
        if container.get("enableX11"):
            environment.append(f"DISPLAY={environ['DISPLAY']}")
        return environment

    def _validate_memory_limit(self, container):
        memory_limit = container.get("memoryLimit")
        if memory_limit and not re.match(r'^\d+[bkmgt]$', memory_limit.lower()):
            return f"Invalid memory limit: {memory_limit}. Valid examples are: 100000b, 1000k, 128m, 1g."
        return memory_limit
