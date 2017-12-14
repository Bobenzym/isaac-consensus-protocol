import argparse
import collections
import colorlog
import configparser
import logging
import pathlib
import sys
import uuid

from bos_consensus.network import (
    BOSNetHTTPServer,
    BOSNetHTTPServerRequestHandler,
)
from bos_consensus.node import Node
from bos_consensus.util import get_local_ipaddress


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

log_handler = colorlog.StreamHandler()
log_handler.setFormatter(
    colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    ),
)

logging.root.handlers = [log_handler]

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-debug', action='store_true')
parser.add_argument('conf', help='ini config file for server node')


if __name__ == '__main__':
    log_level = logging.ERROR
    if '-debug' in sys.argv[1:]:
        log_level = logging.DEBUG

    log.root.setLevel(log_level)

    options = parser.parse_args()
    log.debug('options: %s', options)

    config = collections.namedtuple(
        'Config',
        ('node_id', 'port', 'threshold', 'validators'),
    )(uuid.uuid1().hex, 8001, 51, [])

    if not pathlib.Path(options.conf).exists():
        parser.error('conf file, `%s` does not exists.' % options.conf)

    if not pathlib.Path(options.conf).is_file():
        parser.error('conf file, `%s` is not valid file.' % options.conf)

    conf = configparser.ConfigParser()
    conf.read(options.conf)
    log.info('conf file, `%s` was loaded', options.conf)

    config = config._replace(node_id=conf['node']['id'])
    config = config._replace(port=int(conf['node']['port']))
    config = config._replace(threshold=int(conf['node']['threshold_percent']))
    log.debug('loaded conf: %s', config)

    validator_list = []
    for i in filter(lambda x: len(x.strip()) > 0, conf['node']['validator_list'].split(',')):
        validator_list.append(i.strip())

    config = config._replace(validators=validator_list)
    log.debug('Validators: %s' % config.validators)

    nd = Node(
        config.node_id,
        (get_local_ipaddress(), config.port),
        config.threshold,
        config.validators,
    )

    httpd = BOSNetHTTPServer(nd, ('0.0.0.0', config.port), BOSNetHTTPServerRequestHandler)

    httpd.serve_forever()