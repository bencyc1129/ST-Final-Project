import unittest
import asyncio

from app.objects.c_agent import Agent
from app.objects.c_ability import Ability
from app.objects.secondclass.c_executor import Executor

class TestAgent(unittest.TestCase):
    agent = Agent(paw='123', sleep_min=2, sleep_max=8, watchdog=0, executors=['pwsh', 'psh'], platform='windows',upstream_dest='http://127.0.0.1:9000')

    def test_is_global_variable(self):
        self.assertTrue(self.agent.is_global_variable('payload:whoami'))
        self.assertFalse(self.agent.is_global_variable('payload'))
        self.assertTrue(self.agent.is_global_variable('server'))
        self.assertFalse(self.agent.is_global_variable('client'))
    
    def test_upstream_dest(self):
        self.assertEqual(self.agent.upstream_dest, 'http://127.0.0.1:9000')
    
    def test_calculate_sleep(self):
        async def run_test():
            time = await self.agent.calculate_sleep()
            self.assertTrue(time >= 2 and time <= 8)
        asyncio.run(run_test())

    def test_capabilities(self):
        async def run_test(abilities, expected):
            capabilities = await self.agent.capabilities(abilities)
            if not expected:
                self.assertEqual(capabilities, [])
                return
            for e in expected:
                self.assertTrue(e in capabilities)

        abilities = []
        asyncio.run(run_test(abilities, []))

        executor = Executor(name='psh', platform='windows', command='whoami')
        ability = Ability(ability_id='123', executors=[executor], privilege='Elevated')
        abilities.append(ability)
        asyncio.run(run_test(abilities, []))

        executor = Executor(name = 'sh', platform = 'centOS',command='whoami')
        ability = Ability(ability_id='124', executors=[executor], privilege='User')
        abilities.append(ability)
        asyncio.run(run_test(abilities, []))

        executor = Executor(name = 'psh', platform = 'windows',command='whoami')
        ability1 = Ability(ability_id='125', executors=[executor], privilege='User')
        abilities.append(ability1)
        executor = Executor(name = 'psh', platform = 'windows',command='hostname')
        ability2 = Ability(ability_id='126', executors=[executor], privilege='User')
        abilities.append(ability2)
        asyncio.run(run_test(abilities, [ability1,ability2]))
    
    def test_get_preferred_executor(self):
        async def run_test(ability, expected):
            executor = await self.agent.get_preferred_executor(ability)
            self.assertEqual(executor, expected)
        
        executor = Executor(name = 'sh', platform = 'centOS',command='whoami')
        ability = Ability(ability_id='123', executors=[executor], privilege='User')
        asyncio.run(run_test(ability, None))

        executor = Executor(name = 'psh', platform = 'windows',command='whoami')
        ability = Ability(ability_id='123', executors=[executor], privilege='User')
        asyncio.run(run_test(ability, executor))

        executor = Executor(name = 'pwsh', platform = 'windows',command='whoami')
        ability = Ability(ability_id='123', executors=[executor], privilege='User')
        asyncio.run(run_test(ability, executor))
    
    def test(self):
        pass