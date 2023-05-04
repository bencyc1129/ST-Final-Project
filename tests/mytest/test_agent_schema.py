import unittest

from app.objects.c_agent import  AgentSchema, Agent

class TestAgentFieldsSchema(unittest.TestCase):
    agent = Agent(paw='123', sleep_min=2, sleep_max=8, watchdog=0, executors=['pwsh', 'psh'], platform='windows')

    def test_remove_nulls(self):
        ser_agent = self.agent.schema.dump(self.agent)
        ser_agent['Test'] = None
        self.assertIn('Test',ser_agent.keys())
        self.assertIsNone(ser_agent['Test'])
        removed = self.agent.schema.remove_nulls(ser_agent)
        self.assertNotIn('Test',removed.keys())

    def test_remove_properties(self):
        ser_agent = self.agent.schema.dump(self.agent)
        self.assertIn('display_name',ser_agent.keys())
        self.assertIn('created',ser_agent.keys())
        self.assertIn('last_seen',ser_agent.keys())
        self.assertIn('links',ser_agent.keys())
        removed = self.agent.schema.remove_properties(ser_agent)
        self.assertNotIn('display_name',removed.keys())
        self.assertNotIn('created',removed.keys())
        self.assertNotIn('last_seen',removed.keys())
        self.assertNotIn('links',removed.keys())

class TestAgentSchema(unittest.TestCase):
    schema = AgentSchema()

    def test_build_agent(self):
        data={'paw':'123', 'sleep_min':2, 'sleep_max':8, 'watchdog':0, 'executors':['pwsh', 'psh'], 'platform':'windows'}
        agent = self.schema.build_agent(data,partial=True)
        self.assertIsNone(agent)
        agent = self.schema.build_agent(data,partial=False)
        _agent = Agent(paw='123', sleep_min=2, sleep_max=8, watchdog=0, executors=['pwsh', 'psh'], platform='windows')
        self.assertEqual(agent.schema.dump(agent), _agent.schema.dump(_agent))