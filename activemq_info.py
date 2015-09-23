#!/usr/bin/env python
# collectd-activemq-python
# ========================
#
# Python-based plugin to put ActiveMQ stats to collectd
#
# https://github.com/powdahound/redis-collectd-plugin - was used as template
# https://github.com/kipsnak/munin-activemq-plugin - was used as inspiration

import pprint
from xml.dom import minidom
import urllib

PLUGIN_NAME = 'activemq_info'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    host = args.host
    port = args.port
    log.debug('Using host {0}'.format(host))
    log.debug('Using port {0}'.format(port))
    amq = AMQMonitor(host=host, port=port, verbose_logging=True)
    log.debug('Metrics to send:\n{0}'.format(
        pprint.pformat(amq.fetch_metrics(), indent=2)))


class AMQMonitor(object):
    def __init__(self, host='localhost', port=8161, verbose_logging=False):
        self.host = host
        self.port = port
        self.verbose_logging = verbose_logging

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        log.info('activemq_info plugin [verbose]: %s' % msg)

    def fetch_metrics(self):
        """Connect to ActiveMQ admin webpage and return DOM object"""
        url = 'http://%s:%s/admin/xml/queues.jsp' % (self.host, self.port)
        dom = None
        try:
            dom = minidom.parse(urllib.urlopen(url))
        except Exception:
            self.log_verbose('activemq_info plugin: No info received, '
                             'offline node or turned off ActiveMQ')
            return

        queuenodes = dom.getElementsByTagName("queue")

        gauges = []
        counters = []

        for node in queuenodes:
            queue = node.attributes.item(0).value.replace('.', '_')
            stats_item = node.getElementsByTagName('stats').item(0)
            size = stats_item.getAttribute('size')
            consumerCount = stats_item.getAttribute('consumerCount')
            enqueueCount = stats_item.getAttribute('enqueueCount')
            dequeueCount = stats_item.getAttribute('dequeueCount')

            gauges.append((queue, 'size', size))
            gauges.append((queue, 'consumerCount', consumerCount))
            counters.append(queue, 'enqueueCount',  enqueueCount)
            counters.append(queue, 'dequeueCount',  dequeueCount)

        metrics = {
            'gauges': gauges,
            'counters': counters,
        }
        return metrics

if __name__ == '__main__':
    import argparse
    import logging

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger(__name__)
    main()
else:
    import collectd

    log = collectd
    amq = AMQMonitor()

    def config_callback(conf):
        """Collectd config callback."""
        for node in conf.children:
            if node.key == 'Host':
                amq.host = node.values[0]
            elif node.key == 'Port':
                amq.port = int(node.values[0])
            elif node.key == 'Verbose':
                amq.verbose_logging = bool(node.values[0])
            else:
                log.warning('activemq_info plugin: Unknown config key: %s.'
                            % node.key)
        amq.log_verbose('Configured with host={0}, port={1}'.format(
            amq.host, amq.port))
        collectd.register_read(read_callback)

    def read_callback(self):
        """Collectd read callback"""
        amq.log_verbose('Read callback called')
        metrics = amq.fetch_metrics()
        if metrics is None:
            amq.log_verbose('No metrics returned.')
            return

        for gauge in metrics['gauges']:
            self.dispatch_value(amq, gauge[0], 'gauge', gauge[1], gauge[2])

        for counter in metrics['counters']:
            self.dispatch_value(
                amq, counter[0], 'counter', counter[1], counter[2])

    def dispatch_value(amq, plugin_instance, value_type, instance, value):
        """Dispatch a value to collectd"""
        amq.log_verbose('Sending value: %s.%s.%s=%s'
                        % (PLUGIN_NAME, plugin_instance, instance, value))
        val = collectd.Values(plugin=PLUGIN_NAME)
        val.plugin_instance = plugin_instance
        val.type = value_type
        val.type_instance = instance
        val.values = [value, ]
        val.dispatch()

    amq = AMQMonitor()
    collectd.register_config(config_callback)
