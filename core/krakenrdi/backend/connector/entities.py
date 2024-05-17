from typing import List, Dict, Optional
import re
import logging

# Setup logging
logging.basicConfig(filename='core/logs/krakenrdi.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Image:
    def __init__(self, 
                 buildName: Optional[str] = None,
                 buildArgs: Optional[Dict[str, str]] = None,
                 buildScope: Optional[str] = None,
                 memoryLimit: Optional[str] = None,
                 extraHostIP: Optional[str] = None,
                 startSSH: bool = False,
                 startPostgres: bool = False):
        """
        Initialize an Image instance.

        :param buildName: Name of the build.
        :param buildArgs: Dictionary of build arguments.
        :param buildScope: Scope of the build.
        :param memoryLimit: Memory limit for the build.
        :param extraHostIP: Extra host IP for the build.
        :param startSSH: Flag to start SSH.
        :param startPostgres: Flag to start PostgreSQL.
        """
        self.buildName = buildName
        self.buildArgs = buildArgs if buildArgs is not None else {}
        self.buildScope = buildScope
        self.memoryLimit = memoryLimit
        self.extraHostIP = extraHostIP
        self.startSSH = startSSH
        self.startPostgres = startPostgres

    def validate(self) -> bool:
        """
        Validate the Image instance.

        :return: True if valid, False otherwise.
        """
        if not self.buildName:
            logger.error("Validation error: buildName is required.")
            return False

        if self.memoryLimit and not re.match(r'^\d+[bkmgt]$', self.memoryLimit.lower()):
            logger.error(f"Validation error: Invalid memory limit {self.memoryLimit}.")
            return False

        # Add other validation logic as needed
        return True

class Container:
    def __init__(self, 
                 buildName: Optional[str] = None,
                 containerName: Optional[str] = None,
                 autoRemove: bool = False,
                 capAdd: Optional[List[str]] = None,
                 capDrop: Optional[List[str]] = None,
                 hostname: Optional[str] = None,
                 memoryLimit: Optional[str] = None,
                 networkMode: str = "bridge",
                 networkDisabled: bool = False,
                 readOnly: bool = False,
                 ports: Optional[Dict[str, str]] = None,
                 volumes: Optional[List[str]] = None,
                 tty: bool = True,
                 privileged: bool = False,
                 startSSH: bool = False,
                 startPostgres: bool = False):
        """
        Initialize a Container instance.

        :param buildName: Name of the build.
        :param containerName: Name of the container.
        :param autoRemove: Flag to auto-remove the container.
        :param capAdd: List of capabilities to add.
        :param capDrop: List of capabilities to drop.
        :param hostname: Hostname for the container.
        :param memoryLimit: Memory limit for the container.
        :param networkMode: Network mode for the container.
        :param networkDisabled: Flag to disable the network.
        :param readOnly: Flag to make the container read-only.
        :param ports: Dictionary of ports.
        :param volumes: List of volumes.
        :param tty: Flag to enable TTY.
        :param privileged: Flag to make the container privileged.
        :param startSSH: Flag to start SSH.
        :param startPostgres: Flag to start PostgreSQL.
        """
        self.buildName = buildName
        self.containerName = containerName
        self.autoRemove = autoRemove
        self.capAdd = capAdd if capAdd is not None else []
        self.capDrop = capDrop if capDrop is not None else []
        self.hostname = hostname
        self.memoryLimit = memoryLimit
        self.networkMode = networkMode
        self.networkDisabled = networkDisabled
        self.readOnly = readOnly
        self.ports = ports if ports is not None else {}
        self.volumes = volumes if volumes is not None else []
        self.tty = tty
        self.privileged = privileged
        self.startSSH = startSSH
        self.startPostgres = startPostgres

    def validate(self) -> bool:
        """
        Validate the Container instance.

        :return: True if valid, False otherwise.
        """
        if not self.buildName:
            logger.error("Validation error: buildName is required.")
            return False

        if not self.containerName:
            logger.error("Validation error: containerName is required.")
            return False

        if self.capAdd == ["ALL"]:
            logger.warning("Container is adding all capabilities, which is a security risk.")
            return False

        if self.memoryLimit and not re.match(r'^\d+[bkmgt]$', self.memoryLimit.lower()):
            logger.error(f"Validation error: Invalid memory limit {self.memoryLimit}.")
            return False

        # Add other validation logic as needed
        return True

class Tool:
    def __init__(self, 
                 buildName: Optional[str] = None,
                 buildTag: Optional[str] = None,
                 buildDate: Optional[str] = None,
                 buildScope: Optional[str] = None):
        """
        Initialize a Tool instance.

        :param buildName: Name of the build.
        :param buildTag: Tag of the build.
        :param buildDate: Date of the build.
        :param buildScope: Scope of the build.
        """
        self.buildName = buildName
        self.buildTag = buildTag
        self.buildDate = buildDate
        self.buildScope = buildScope

    def validate(self) -> bool:
        """
        Validate the Tool instance.

        :return: True if valid, False otherwise.
        """
        if not self.buildName:
            logger.error("Validation error: buildName is required.")
            return False

        if not self.buildTag:
            logger.error("Validation error: buildTag is required.")
            return False

        # Add other validation logic as needed
        return True
