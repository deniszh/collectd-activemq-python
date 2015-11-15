# collectd-activemq-python
# ========================
#
# Python-based plugin to put ActiveMQ stats to collectd
#
# https://github.com/powdahound/redis-collectd-plugin - was used as template
# https://github.com/kipsnak/munin-activemq-plugin - was used as inspiration

from xml.dom import minidom
import requests


class AMQMonitor(object):
    def __init__(self, plugin_name='activemq_info', host='localhost', port=8161, webadmin='admin', login='', passw='',
                 verbose_logging=False):
        self.plugin_name = plugin_name
        self.host = host
        self.port = port
        self.webadmin = webadmin
        self.login = login
        self.passw = passw
        self.verbose_logging = verbose_logging

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        elif __name__ == '__main__':
            print msg
        else:
            collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        """Receive configuration block"""
        for node in conf.children:
            if node.key == 'Host':
                self.host = node.values[0]
            elif node.key == 'Port':
                self.port = int(node.values[0])
            elif node.key == 'User':
                self.login = node.values[0]
            elif node.key == 'Pass':
                self.passw = node.values[0]
            elif node.key == 'Webadmin':
                self.webadmin = node.values[0]
            elif node.key == 'Verbose':
                self.verbose_logging = bool(node.values[0])
            else:
                collectd.warning('%s plugin: Unknown config key: %s.' % (self.plugin_name, node.key))
        self.log_verbose('Configured with host=%s, port=%s, webadmin=%s, login=%s' % (
            self.host, self.port, self.webadmin, self.login))

    def dispatch_value(self, plugin_instance, value_type, instance, value):
        """Dispatch a value to collectd"""
        self.log_verbose('Sending value: %s.%s.%s=%s' % (self.plugin_name, plugin_instance, instance, value))
        if __name__ == "__main__":
            return
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = value_type
        val.type_instance = instance
        val.values = [value, ]
        val.dispatch()

    def fetch_metrics(self):
        """Connect to ActiveMQ admin webpage and return DOM object"""
        url = 'http://%s:%s/%s/xml/queues.jsp' % (self.host, self.port, self.webadmin)
        try:
            if self.login:
                dom = minidom.parseString(requests.get(url, auth=(self.login, self.passw)).text)
            else:
                dom = minidom.parseString(requests.get(url).text)
        except Exception:
            self.log_verbose('%s plugin: No info received, offline node or turned off ActiveMQ' % self.plugin_name)
            return

        queuenodes = dom.getElementsByTagName('queue')

        gauges = []
        counters = []

        for node in queuenodes:
            queue = node.attributes.item(0).value.replace('.', '_')
            stats_item = node.getElementsByTagName('stats').item(0)
            size = stats_item.getAttribute('size')
            consumer_count = stats_item.getAttribute('consumerCount')
            enqueue_count = stats_item.getAttribute('enqueueCount')
            dequeue_count = stats_item.getAttribute('dequeueCount')

            gauges.append((queue, 'size', size))
            gauges.append((queue, 'consumerCount', consumer_count))
            counters.append((queue, 'enqueueCount',  enqueue_count))
            counters.append((queue, 'dequeueCount',  dequeue_count))

        metrics = {
            'gauges': gauges,
            'counters': counters,
        }
        return metrics

    def read_callback(self):
        """Collectd read callback"""
        self.log_verbose('Read callback called')
        metrics = self.fetch_metrics()
        if metrics is None:
            self.log_verbose('No metrics returned.')
            return

        for gauge in metrics['gauges']:
            self.dispatch_value(gauge[0], 'gauge', gauge[1], gauge[2])

        for counter in metrics['counters']:
            self.dispatch_value(counter[0], 'counter', counter[1], counter[2])


if __name__ == "__main__":
    import argparse

    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('host')
        parser.add_argument('port', type=int)
        parser.add_argument('-w', '--webadmin', default='admin')
        parser.add_argument('-l', '--login')
        parser.add_argument('-p', '--password')
        return parser.parse_args()

    args = parse_args()
    amq = AMQMonitor(host=args.host, port=args.port, webadmin=args.webadmin, login=args.login, passw=args.password,
                     verbose_logging=True)
    amq.read_callback()

else:
    import collectd
    amq = AMQMonitor()
    # register callbacks
    collectd.register_config(amq.configure_callback)
    collectd.register_read(amq.read_callback)