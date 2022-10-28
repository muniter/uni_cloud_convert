#!/usr/bin/python3
import os
import subprocess

PATH = "./assets"
NFS_NEEDS = ["api", "converter"]


def check_root():
    if os.geteuid() != 0:
        print("Please run as root, sudo foooo")
        exit(1)


def setup_nfs_mount():
    hostname = os.uname().nodename
    if hostname not in NFS_NEEDS:
        print("Skipping NFS mount setup, {} is not in {}".format(hostname, NFS_NEEDS))
        return

    if not os.path.exists(PATH):
        os.makedirs(PATH)

    out = subprocess.run(
        "df | grep 'nfs'",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if out.returncode != 0:
        print("nfs share mount not found, trying to mount")
        out = subprocess.run(["mount", "-t", "nfs", "nfs:/", PATH])
        if out.returncode != 0:
            print("Failed to mount the nfs share")
            exit(1)
        else:
            print("nfs share mounted successfully")
    else:
        print("nfs share already mounted")


def get_docker_command():
    COMPOSE_CMD: list[str]
    out = subprocess.run(
        ["which", "docker-compose"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if out.returncode == 0:
        COMPOSE_CMD = ["docker-compose"]
    else:
        # Let's try with docker compose
        cmd = ["docker", "compose"]
        out = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if out.returncode == 0:
            COMPOSE_CMD = cmd
        else:
            print("Failed to find 'docker-compose' or 'docker compose'")
            exit(1)

    return COMPOSE_CMD


def start_docker_compose():
    out = subprocess.run(get_docker_command() + ["up", "-d"], shell=False, check=False)
    if out.returncode != 0:
        print("Failed to start the docker compose")
        exit(1)


def main():
    check_root()
    setup_nfs_mount()
    start_docker_compose()


if __name__ == "__main__":
    main()
