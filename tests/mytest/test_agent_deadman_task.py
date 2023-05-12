import unittest
from unittest.mock import patch
import asyncio

from app.objects.c_agent import Agent
from app.service.data_svc import DataService
from app.objects.c_ability import Ability
from app.objects.secondclass.c_executor import Executor
from app.objects.secondclass.c_fact import Fact

class TestAgent(unittest.TestCase):
    agent = Agent()
    '''Test deadman function
    - by mocking task function, we can test line 250-256
    '''
    @patch('app.service.data_svc.DataService.locate')
    @patch('app.objects.c_agent.Agent.task')
    def test_deadman(self, mock_task, mock_locate):
        async def run_test(data_svc):
            await self.agent.deadman(data_svc=data_svc)
        
        data_svc = DataService()
        mock_locate.return_value = [Ability(ability_id='36eecb80-ede3-442b-8774-956e906aff02', executors=[Executor(name='psh', platform='windows', command='whoami')], privilege='User')]
        mock_task.return_value = None
        self.agent.set_config(name='agents', prop='deadman_abilities', value=['36eecb80-ede3-442b-8774-956e906aff02'])
        asyncio.run(run_test(data_svc))

    '''Test task function
    - when Agent.executors is [] : line 259-260
    - when Ability is exists : line 261-285
        - when Fact is exists : line 281-283
        - when executor is psh : line 342-343
    - when executor is sh : line 344-345
    - when executor is not psh or sh : line 346
    '''
    @patch('app.service.knowledge_svc.KnowledgeService.add_fact')
    @patch('app.utility.base_planning_svc.BasePlanningService.obfuscate_commands')
    def test_task(self, mock_obfuscate_commands, mock_add_fact):
        async def run_test(abilities, obfuscator, facts=(), deadman=False):
            links = await self.agent.task(abilities=abilities, obfuscator=obfuscator, facts=facts, deadman=deadman)
            return links

        self.agent.executors = []
        mock_obfuscate_commands.return_value = []
        self.assertEqual([], asyncio.run(run_test(abilities=[], obfuscator='plain-text', facts=(), deadman=False)))

        self.agent.platform = 'windows'
        self.agent.executors = ['psh']
        mock_obfuscate_commands.return_value = []
        mock_add_fact.return_value = None
        self.assertEqual([], asyncio.run(run_test(abilities=[Ability(ability_id='36eecb80-ede3-442b-8774-956e906aff02', executors=[Executor(name='psh', platform='windows', command='whoami')], privilege='User')],
                             obfuscator='plain-text',
                             facts=[Fact(trait='host.user.name', value='test', score=1, collected_by='123', technique_id='123', source='123')],
                             deadman=False)))
        
        self.agent.platform = 'linux'
        self.agent.executors = ['sh']
        self.assertEqual([], asyncio.run(run_test(abilities=[], obfuscator='plain-text', facts=(), deadman=False)))

        
        self.agent.platform = 'linux'
        self.agent.executors = ['bash']
        self.assertEqual([], asyncio.run(run_test(abilities=[], obfuscator='plain-text', facts=(), deadman=False)))