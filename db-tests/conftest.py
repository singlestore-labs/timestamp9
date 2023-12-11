import logging
import os
import subprocess
import time
from typing import Optional, Literal

import pytest
import singlestoredb as s2
from singlestoredb.connection import Connection

logger = logging.getLogger(__name__)

STARTUP_CONNECT_ATTEMPTS = 10
STARTUP_CONNECT_TIMEOUT_SECONDS = 2

TEARDOWN_WAIT_ATTEMPTS = 20
TEARDOWN_WAIT_SECONDS = 2

EXECUTION_MODE = Literal["sequential", "leader", "follower"]


# Look for pytest-xdist environment variables and figure out what
# mode we're running in
@pytest.fixture(scope="session")
def execution_mode() -> EXECUTION_MODE:
    if "PYTEST_XDIST_WORKER" in os.environ and "PYTEST_XDIST_WORKER_COUNT" in os.environ:
        worker = os.environ["PYTEST_XDIST_WORKER"]
        logger.debug(f"PYTEST_XDIST_WORKER == {worker}")
        worker_count = os.environ["PYTEST_XDIST_WORKER_COUNT"]
        logger.debug(f"PYTEST_XDIST_WORKER_COUNT == {worker_count}")

        if worker_count == "1":
            return "sequential"
        elif worker == "gw0":
            return "leader"
        else:
            return "follower"
    else:
        logger.debug("XDIST environment vars not found")
        return "sequential"


# Look for pytest-xdist environment variables to choose a name
# for this worker node
@pytest.fixture(scope="session")
def node_name():
    if "PYTEST_XDIST_WORKER" in os.environ:
        worker = os.environ["PYTEST_XDIST_WORKER"]
        logger.debug(f"PYTEST_XDIST_WORKER == {worker}")
        return worker
    else:
        logger.debug("XDIST environment vars not found")
        return "master"


class _TestContainerManager():
    """Manages the setup and teardown of a SingleStoreDB Dev Container

    Requires docker to be available on the local system.
    """
    def __init__(self):
        self.container_name = "singlestoredb-test-container"
        self.dev_image_name = "ghcr.io/singlestore-labs/singlestoredb-dev"

        assert "SINGLESTORE_LICENSE" in os.environ, "SINGLESTORE_LICENSE not set"

        self.root_password = "Q8r4D7yXR8oqn"
        self.environment_vars = {
            "SINGLESTORE_LICENSE": None,
            "ROOT_PASSWORD": f"\"{self.root_password}\"",
            "SINGLESTORE_SET_GLOBAL_DEFAULT_PARTITIONS_PER_LEAF": "1"
        }

        self.ports = ["3306", "8080", "9000"]

        self.url = f"root:{self.root_password}@127.0.0.1:3306"

    def start(self):
        command = ' '.join(self._start_command())

        logger.info(f"Starting container {self.container_name}")
        try:
            license = os.environ["SINGLESTORE_LICENSE"]
            logger.info(f"len(SL) = {len(license)}")
            env = {
                "SINGLESTORE_LICENSE": license
            }
            subprocess.check_call(command, shell=True, env=env)
        except Exception as e:
            logger.exception(e)
            raise RuntimeError("Failed to start container. Is one already running?") from e
        logger.debug("Container started")


    def _start_command(self):
        yield "docker run -d --name"
        yield self.container_name
        for key, value in self.environment_vars.items():
            yield "-e"
            if value is None:
                yield key
            else:
                yield f"{key}={value}"

        for port in self.ports:
            yield "-p"
            yield f"{port}:{port}"

        yield self.dev_image_name

    def print_logs(self):
        logs_command = ["docker", "logs", self.container_name]
        logger.info(f"Getting logs")
        logger.info(subprocess.check_output(logs_command))

    def connect(self):
        # Run all but one attempts trying again if they fail
        for i in range(STARTUP_CONNECT_ATTEMPTS - 1):
            try:
                return s2.connect(self.url)
            except Exception:
                logger.debug(f"Database not available yet (attempt #{i}).")
                time.sleep(STARTUP_CONNECT_TIMEOUT_SECONDS)
        else:
            # Try one last time and report error if it fails
            try:
                return s2.connect(self.url)
            except Exception as e:
                logger.error("Timed out while waiting to connect to database.")
                logger.exception(e)
                self.print_logs()
                raise RuntimeError("Failed to connect to database") from e

    def wait_till_connections_closed(self):
        heart_beat = s2.connect(self.url)
        for i in range(TEARDOWN_WAIT_ATTEMPTS):
            connections = self.get_open_connections(heart_beat)
            logger.debug(f"Waiting for other connections (n={connections-1}) to close (attempt #{i})")
            time.sleep(TEARDOWN_WAIT_SECONDS)
        else:
            logger.warning("Timed out while waiting for other connections to close")
            self.print_logs()

    def get_open_connections(self, conn: Connection) -> Optional[int]:
        for row in conn.show.status(extended=True):
            logger.info(f"{row['Name']} = {row['Value']}")
            if row['Name'] == 'Threads_connected':
                return int(row['Value'])
        
        return None

    def stop(self):
        logger.info("Cleaning up SingleStore DB dev container")
        logger.debug("Stopping container")
        try:
            subprocess.check_call(f"docker stop {self.container_name}", shell=True)
        except Exception as e:
            logger.exception(e)
            raise RuntimeError("Failed to stop container.") from e

        logger.debug("Removing container")
        try:
            subprocess.check_call(f"docker rm {self.container_name}", shell=True)
        except Exception as e:
            logger.exception(e)
            raise RuntimeError("Failed to stop container.") from e


@pytest.fixture(scope="session")
def singlestoredb_test_container(execution_mode: EXECUTION_MODE):
    container_manager = _TestContainerManager()

    # In sequential operation do all the steps
    if execution_mode == "sequential":
        logger.debug("Not distributed")
        container_manager.start()
        yield container_manager
        container_manager.stop()
    # In distributed execution as leader,
    # do the steps but wait for other workers before stopping
    elif execution_mode == "leader":
        logger.debug("Distributed leader")
        container_manager.start()
        yield container_manager
        container_manager.wait_till_connections_closed()
        container_manager.stop()
    # In distributed exeuction as a non-leader,
    # don't worry about the container lifecycle
    elif execution_mode == "follower":
        logger.debug("Distributed follower")
        yield container_manager

    else:
        raise ValueError(f"Invalid execution mode '{execution_mode}'")


@pytest.fixture(scope="session")
def singlestoredb_connection(singlestoredb_test_container: _TestContainerManager):
    connection = singlestoredb_test_container.connect()
    logger.debug(f"Connected to database.")

    yield connection

    logger.debug("Closing connection")
    connection.close()


class _NameAllocator():
    def __init__(self, id):
        self.id = id
        self.names = 0

    def get_name(self) -> str:
        name = f"x_db_{self.id}_{self.names}"
        self.names += 1
        return name


@pytest.fixture(scope="session")
def name_allocator(node_name: str):
    yield _NameAllocator(node_name)


@pytest.fixture
def singlestoredb_tempdb(singlestoredb_connection: Connection, name_allocator: _NameAllocator):
    assert singlestoredb_connection.is_connected(), "Database is no longer connected"
    db = name_allocator.get_name()

    with singlestoredb_connection.cursor() as cursor:
        logger.debug(f"Creating temporary DB \"{db}\"")
        cursor.execute(f"CREATE DATABASE {db}")
        cursor.execute(f"USE {db}")

        yield cursor
        
        logger.debug(f"Dropping temporary DB \"{db}\"")
        cursor.execute(f"DROP DATABASE {db}")

