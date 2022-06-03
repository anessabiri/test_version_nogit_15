#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
import logging
import requests
import sys
from http.client import HTTPConnection
from .core.core import CLI, CVAT_API_V1
from .core.definition import parser, get_auth
log = logging.getLogger(__name__)


def config_log(level):
    log = logging.getLogger('core')
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(level)
    if level <= logging.DEBUG:
        HTTPConnection.debuglevel = 1


def main():
    actions = {'create': CLI.tasks_create,
               'delete': CLI.tasks_delete,
               'ls': CLI.tasks_list,
               'ls_users': CLI.users_list,
               'update_assignee': CLI.update_assignee,
               'update_reviewer': CLI.update_reviewer,
               'projects': CLI.projects_list,
               'frames': CLI.tasks_frame,
               'dump': CLI.tasks_dump,
               'upload': CLI.tasks_upload}
    args = parser.parse_args()
    config_log(args.loglevel)
    with requests.Session() as session:
        session.auth = args.auth
        api = CVAT_API_V1(args.server_host, args.server_port)
        cli = CLI(session, api)
        try:
            actions[args.action](cli, **args.__dict__)
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            log.critical(e)

def nested_command(parameters):
    actions = {'create': CLI.tasks_create,
               'delete': CLI.tasks_delete,
               'ls': CLI.tasks_list,
               'ls_users': CLI.users_list,
               'update_assignee': CLI.update_assignee,
               'update_reviewer': CLI.update_reviewer,
               'projects': CLI.projects_list,
               'frames': CLI.tasks_frame,
               'dump': CLI.tasks_dump,
               'upload': CLI.tasks_upload,
               'export': CLI.tasks_export}
    config_log(parameters['loglevel'])
    with requests.Session() as session:
        session.auth = get_auth(parameters['auth'])
        api = CVAT_API_V1(parameters['server-host'], parameters['server-port'])
        cli = CLI(session, api)
        try:
            if parameters['return']:
                result = actions[parameters['action']](cli, **parameters)
                return result
            else:
                actions[parameters['action']](cli, **parameters)
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            log.critical(e)


if __name__ == '__main__':
    main()
