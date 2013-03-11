# collectd-activemq-python
# ========================
#
# Python-based plugin to put ActiveMQ stats to collectd
#
# https://github.com/powdahound/redis-collectd-plugin - was used as template
# https://github.com/kipsnak/munin-activemq-plugin - was used as inspiration

import collectd
from xml.dom import minidom
import urllib


class AMQMonitor(object):

    def __init__(self):
        self.plugin_name = "activemq_info"
        self.amq_admin_host = 'localhost'
        self.amq_admin_port = 8161
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('activemq_info plugin [verbose]: %s' % msg)

    def configure_callback(self, conf):
        """Receive configuration block"""
        for node in conf.children:
            if node.key == 'Host':
                self.amq_admin_host = node.values[0]
            elif node.key == 'Port':
                self.amq_admin_port = int(node.values[0])
            elif node.key == 'Verbose':
                self.verbose_logging  = bool(node.values[0])
            else:
                collectd.warning('activemq_info plugin: Unknown config key: %s.' % node.key)
        self.log_verbose('Configured with host=%s, port=%s' % (self.amq_admin_host, self.amq_admin_port))


    def dispatch_value(self, plugin_instance, value_type, instance, value):
        """Dispatch a value to collectd"""
        self.log_verbose('Sending value: %s.%s.%s=%s' % (self.plugin_name, plugin_instance, instance, value))
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = value_type
        val.type_instance = instance
        val.values = [value, ]
        val.dispatch()


    def fetch_info(self):
        """Connect to ActiveMQ admin webpage and return DOM object"""
        url = 'http://%s:%s/admin/xml/queues.jsp' % (self.amq_admin_host, self.amq_admin_port)
        dom = None
        try:
            dom = minidom.parse(urllib.urlopen(url))
            #dom = minidom.parse(open('queues.xml', 'r'))
        except Exception:
            pass
        return dom


    def read_callback(self):
        """Collectd read callback"""
        self.log_verbose('Read callback called')
        dom = self.fetch_info()
        if not dom:
            self.log_verbose('activemq_info plugin: No info received, offline node or turned off ActiveMQ')
            return

        queuenodes = dom.getElementsByTagName("queue")
        for node in queuenodes:
            queue = node.attributes.item(0).value.replace('.', '_')
            size = node.getElementsByTagName("stats").item(0).getAttribute("size")
            consumerCount = node.getElementsByTagName("stats").item(0).getAttribute("consumerCount")
            enqueueCount = node.getElementsByTagName("stats").item(0).getAttribute("enqueueCount")
            dequeueCount = node.getElementsByTagName("stats").item(0).getAttribute("dequeueCount")
            self.dispatch_value(queue, 'gauge',   'size',          size)
            self.dispatch_value(queue, 'gauge',   'consumerCount', consumerCount)
            self.dispatch_value(queue, 'counter', 'enqueueCount',  enqueueCount)
            self.dispatch_value(queue, 'counter', 'dequeueCount',  dequeueCount)


amq = AMQMonitor()
# register callbacks
collectd.register_config(amq.configure_callback)
collectd.register_read(amq.read_callback)
