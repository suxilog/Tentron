# Create your tasks here
import logging

import docker
from celery import shared_task

logger = logging.getLogger("celery")


@shared_task
def run_command_in_container(previous_task_result, container_name, command):
    print(f"Running command {command} in container {container_name}")
    if previous_task_result is not None:
        if previous_task_result[0] != 0:
            print(f"Previous task failed with exit code {previous_task_result}")
            logger.error(f"Previous task failed with exit code {previous_task_result}")
            return previous_task_result
        print(f"Previous task result: {previous_task_result}")
    client = docker.from_env()

    container = client.containers.get(container_name)
    exec_id = container.exec_run(cmd=command, stdout=True, stderr=True)

    if exec_id.exit_code != 0:
        print(f"Error executing command: {exec_id.output.decode()}")
        logger.error(f"Error executing command: {exec_id.output.decode()}")
    else:
        print(f"Command output: {exec_id.output.decode()}")
        logger.info(f"Command output: {exec_id.output.decode()}")

    return exec_id
