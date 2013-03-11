import simplejson as json
from collections import namedtuple

from kazoo.client import KazooClient

ZkKafkaBroker = namedtuple('ZkKafkaBroker', ['id', 'host', 'port'])
ZkKafkaSpout = namedtuple('ZkKafkaSpout', ['id', 'partitions'])
ZkKafkaTopic = namedtuple('ZkKafkaTopic', ['topic', 'broker', 'num_partitions'])

class ZkClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = KazooClient(hosts=':'.join([host, str(port)]))

    @classmethod
    def _zjoin(cls, e):
        return '/'.join(e)

    def brokers(self, broker_root='/brokers'):
        '''
        Returns a dictionary of ZkKafkaBroker tuples, where each key is the broker ID
        and the value is a ZkKafkaBroker.
        '''
        b = {}
        id_root = self._zjoin([broker_root, 'ids'])

        self.client.start()
        for c in self.client.get_children(id_root):
            n = self.client.get(self._zjoin([id_root, c]))[0]
            broker = ZkKafkaBroker._make(n.split(':'))
            b[broker.id] = broker
        self.client.stop()
        return b

    def topics(self, broker_root='/brokers'):
        '''
        Returns a list of ZkKafkaTopic tuples, where each tuple represents
        a topic being stored in a broker.
        '''
        topics = []
        t_root = self._zjoin([broker_root, 'topics'])

        self.client.start()
        for t in self.client.get_children(t_root):
            for b in self.client.get_children(self._zjoin([t_root, t])):
                n = self.client.get(self._zjoin([t_root, t, b]))[0]
                topics.append(ZkKafkaTopic._make([t, b, n]))
        self.client.stop()
        return topics

    def spouts(self, spout_root, topology):
        '''
        Returns a list of ZkKafkaSpout tuples, where each tuple represents
        a Storm Kafka Spout.
        '''
        s = []
        self.client.start()
        for c in self.client.get_children(spout_root):
            partitions = []
            for p in self.client.get_children(self._zjoin([spout_root, c])):
                j = json.loads(self.client.get(self._zjoin([spout_root, c, p]))[0])
                if j['topology']['name'] == topology:
                    partitions.append(j)
            s.append(ZkKafkaSpout._make([c, partitions]))
        self.client.stop()
        return tuple(s)