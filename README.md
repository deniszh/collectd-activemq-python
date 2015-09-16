collectd-activemq-python
========================

Python-based plugin to put simple [ActiveMQ] (http://activemq.apache.org/) stats to [collectd](http://collectd.org)

Data captured includes:

 * Queue name
 * Number of messages in queue
 * Number of consumers
 * Counter of enqueued messages
 * Counter of dequeued messages

[powdahoud's redis-collectd-plugin] (https://github.com/powdahound/redis-collectd-plugin/) was used as template,
[kipsnak's Perl ActiveMQ Munin plugin] (https://github.com/kipsnak/munin-activemq-plugin) - as inspiration. :)

Install
-------
 1. Place activemq_info.py in /usr/lib/collectd/plugins/python
 2. Configure the plugin (see below).
 3. Restart collectd.

Configuration
-------------
Add the following to your collectd config

    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      ModulePath "/usr/lib/collectd/plugins/python"
      Import "activemq_info"

      <Module activemq_info>
        Host "localhost"
        Port 8161
      </Module>
    </Plugin>

License
-------
MIT
