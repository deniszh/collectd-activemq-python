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


# Host to connect to. Override in config by specifying 'Host'.
AMQ_ADMIN_HOST = 'localhost'

# Port to connect on. Override in config by specifying 'Port'.
AMQ_ADMIN_PORT = 8161

# Verbose logging on/off. Override in config by specifying 'Verbose'.
VERBOSE_LOGGING = False


def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('activemq_info plugin [verbose]: %s' % msg)


def configure_callback(conf):
    """Receive configuration block"""
    global AMQ_ADMIN_HOST, AMQ_ADMIN_PORT, VERBOSE_LOGGING
    for node in conf.children:
        if node.key == 'Host':
            AMQ_ADMIN_HOST = node.values[0]
        elif node.key == 'Port':
            AMQ_ADMIN_PORT = int(node.values[0])
        elif node.key == 'Verbose':
            VERBOSE_LOGGING = bool(node.values[0])
        else:
            collectd.warning('activemq_info plugin: Unknown config key: %s.'
                             % node.key)
    log_verbose('Configured with host=%s, port=%s' % (AMQ_ADMIN_HOST, AMQ_ADMIN_PORT))


def dispatch_value(instance, key, value, value_type):
    """Dispatch a value to collectd"""
    log_verbose('Sending value: %s.%s=%s' % (instance, key, value))
    val = collectd.Values(plugin='activemq_info')
    val.plugin_instance = instance
    val.type = value_type
    val.values = [value]
    val.dispatch()


def fetch_info():
    """Connect to ActiveMQ admin webpage and return DOM object"""
    url = 'http://%s:%s/admin/xml/queues.jsp' % (AMQ_ADMIN_HOST, AMQ_ADMIN_PORT)
    dom = None
    try:
        dom = minidom.parse(urllib.urlopen(url))
        #dom = minidom.parse(open('queues.xml', 'r'))
    except Exception:
        pass
    return dom


def read_callback():
    """Collectd read callback"""
    log_verbose('Read callback called')
    dom = fetch_info()
    if not dom:
        log_verbose('activemq_info plugin: No info received, offline node or turned off ActiveMQ')
        return

    queuenodes = dom.getElementsByTagName("queue")
    for node in queuenodes:
        queue = node.attributes.item(0).value
        size = node.getElementsByTagName("stats").item(0).getAttribute("size")
        consumerCount = node.getElementsByTagName("stats").item(0).getAttribute("consumerCount")
        enqueueCount = node.getElementsByTagName("stats").item(0).getAttribute("enqueueCount")
        dequeueCount = node.getElementsByTagName("stats").item(0).getAttribute("dequeueCount")
        dispatch_value(queue, 'size',          size,          'gauge')
        dispatch_value(queue, 'consumerCount', consumerCount, 'gauge')
        dispatch_value(queue, 'enqueueCount',  enqueueCount,  'counter')
        dispatch_value(queue, 'dequeueCount',  dequeueCount,  'counter')


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
