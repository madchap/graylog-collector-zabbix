#!/usr/bin/env python

# Fred Blaise
# Zabbix LLD for graylog collectors

import json
import requests
from requests.auth import HTTPBasicAuth
import ConfigParser
import logging
import os
import base64


def setup_default_logger():
    global logger
    
    logger = logging.getLogger()
    # If you go to INFO or below, the output will break zabbix's parsing
    logger.setLevel(logging.WARN)

    # add console handler
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def read_config():
    """
    Reads configuration file
    :returns ConfigParser object
    """
    config = ConfigParser.ConfigParser()

    try:
        logger.info("Reading configuration file")
        config.read(os.path.dirname(__file__) + "/check_graylog_collector.conf")

        return config
    except ConfigParser.NoSectionError, e:
        logger.error("Could not open or read configuration file: {}".format(e.message))


def graylog_session_login(config):
    session = requests.session()

    logger.info("Logging in to Graylog")
    login_payload = {
        'username': config.get('graylog', 'gl_user'),
        'password': base64.b64decode(config.get('graylog', 'gl_user_pass')),
        'host': ''
    }
    session.headers.update({'Content-type': 'application/json'})
    session.headers.update({'Accept': 'application/json'})
    r = session.post(
        config.get('graylog', 'gl_api') + config.get('graylog', 'gl_sessions_endpoint'),
        json=login_payload,
        verify={'True': True, 'False': False}.get(config.get('ssl', 'ssl_verify'))
    )

    log_response_info(r)
    current_session_id = r.json().get('session_id')

    return session, current_session_id


def graylog_session_logout(session_id, session, config):
    r = session.delete(
        config.get('graylog', 'gl_api') + config.get('graylog', 'gl_sessions_endpoint') + "/" + session_id,
        auth=HTTPBasicAuth(session_id, 'session'),
        verify={'True': True, 'False': False}.get(config.get('ssl', 'ssl_verify'))
    )
    log_response_info(r)


def graylog_get_collectors(session_id, session, config):
    r = session.get(
        config.get('graylog', 'gl_api') + config.get('graylog', 'gl_collectors_endpoint'),
        auth=HTTPBasicAuth(session_id, 'session'),
        verify={'True': True, 'False': False}.get(config.get('ssl', 'ssl_verify'))
    )
    log_response_info(r)

    lld_dict = {}
    lld_dict['data'] = []
    
    if r.status_code == requests.codes.ok:
        r_json = json.loads(r.text)
        for collector in r_json["collectors"]:
            nodeid = collector['node_id']
            logger.info("Found node {}".format(collector.get("node_id")))
            nodestatus = collector['node_details']['status']['status']
            logger.info("Node {} has status {}".format(nodeid, nodestatus))
            nodeactive = collector['active']
            logger.info("Node {} active state {}".format(nodeid, nodeactive))
           
            if (nodestatus == 0) and (nodeactive == False):
                collector = {"{#CLNAME}":"{}".format(nodeid), "{#CSTATUS}":"{}".format(99)}
            else:
                collector = {"{#CLNAME}":"{}".format(nodeid), "{#CSTATUS}":"{}".format(nodestatus)}
            
            lld_dict['data'].append(collector.copy())

    return lld_dict


def log_response_info(r):
    logger.debug("Code={} Headers={} Content={}".format(str(r.status_code), str(r.headers), str(r.content)))


if __name__ == "__main__":
    global logger
    
    logger = setup_default_logger()
    config = read_config()
    
    session, session_id = graylog_session_login(config)
    collectors = graylog_get_collectors(session_id, session, config)
    graylog_session_logout(session_id, session, config)
    
    print json.dumps(collectors, indent=4)
