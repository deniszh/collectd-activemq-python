# collectd-activemq-python
# ========================
#
# Python-based plugin to put ActiveMQ stats to collectd
#
# https://github.com/powdahound/redis-collectd-plugin - was used as template
# https://github.com/kipsnak/munin-activemq-plugin - was used as inspiration

import collectd
import sys
import urllib2
try:
    import xml.etree.cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        print 'python >= 2.5'
        sys.exit()

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
    """Connect to ActiveMQ admin webpage and return XML object"""
    url = 'http://%s:%s/admin/xml/queues.jsp' % (AMQ_ADMIN_HOST, AMQ_ADMIN_PORT)
    xml = None
    try:
        f = urllib2.urlopen(url)
        #f = open('queues.xml', 'r')
        xml = etree.fromstring(f.read())
    except Exception:
        pass
    return xml


def read_callback():
    """Collectd read callback"""
    log_verbose('Read callback called')
    xml = fetch_info()
    if not xml:
        log_verbose('activemq_info plugin: No info received, offline node or turned off ActiveMQ')
        return

    for q in xml.iter('queue'):
        queue = q.attrib['name'].replace('.', '_')
        stat = q.find('stats')
        dispatch_value(queue, 'size',          stat.attrib['size'],          'gauge')
        dispatch_value(queue, 'consumerCount', stat.attrib['consumerCount'], 'gauge')
        dispatch_value(queue, 'enqueueCount',  stat.attrib['enqueueCount'],  'counter')
        dispatch_value(queue, 'dequeueCount',  stat.attrib['dequeueCount'],  'counter')


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
