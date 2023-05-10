import unittest
from unittest.mock import patch
import asyncio
import datetime
import logging

from app.objects.c_agent import Agent
from app.objects.c_ability import Ability
from app.objects.secondclass.c_executor import Executor
from app.service.file_svc import FileSvc
from app.service.data_svc import DataService
from app.service.knowledge_svc import KnowledgeService
from app.service.event_svc import EventService
from app.service.contact_svc import ContactService
from app.utility.base_service import BaseService
from app.utility.base_world import BaseWorld
from app.objects.secondclass.c_fact import Fact

class TestAgent(unittest.TestCase):
    agent = Agent(paw='123', sleep_min=2, sleep_max=8, watchdog=0, executors=['pwsh', 'psh'], platform='windows')

    def test_is_global_variable(self):
        self.assertTrue(self.agent.is_global_variable('payload:whoami'))
        self.assertFalse(self.agent.is_global_variable('payload'))
        self.assertTrue(self.agent.is_global_variable('server'))
        self.assertFalse(self.agent.is_global_variable('client'))
    
    def test_upstream_dest(self):
        self.assertEqual(Agent(paw='123', sleep_min=2, sleep_max=8, watchdog=0, executors=['pwsh', 'psh'], platform='windows',upstream_dest='http://127.0.0.1:9000').upstream_dest, 'http://127.0.0.1:9000')
    
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
    
    def test_heartbeat_modification(self):
        @patch("datetime.datetime")
        async def run_time_test(mock_datetime):
            mock_datetime.utcnow.return_value = datetime.datetime(2020, 1, 1, 0, 0, 0)
            self.agent.trusted = True
            await self.agent.heartbeat_modification()
            self.assertEqual(self.agent.last_seen, '2020-01-01 00:00:00')
        
        async def run_test(**updated):
            await self.agent.heartbeat_modification(**updated)
            for modattr, expected in updated.items():
                self.assertEqual(getattr(self.agent,modattr), expected)
        asyncio.run(run_test(pid='1001',ppid='1002',server='192.168.1.1',exe_name='sandcat.go-windows.exe',
                            location='C:\\Users\\Public\\sandcat.go-windows.exe', privilege='Evlavated',host='Victim',
                            username='VICTIM\\Administrator',platform='linux',architecture='x86_64',proxy_receivers={"p1":["192.168.1.2"]},
                            proxy_chain=[["192.168.1.3"]],deadman_enabled=True,contact='HTTP',host_ip_addrs='127.0.0.1',
                            upstream_dest='http://127.0.0.1:9001',executors=['pwsh', 'psh','sh']))
    
    def test_gui_modification(self):
        async def run_test(**updated):
            await self.agent.gui_modification(**updated)
            for modattr, expected in updated.items():
                self.assertEqual(getattr(self.agent,modattr), expected)
        asyncio.run(run_test(group='red', trusted=True, sleep_min=10, sleep_max=15, watchdog=1, pending_contact='DNS'))

    def test_kill(self):
        async def run_test():
            await self.agent.kill()
            self.assertEqual(self.agent.watchdog,1)
            self.assertEqual(self.agent.sleep_max,60*2)
            self.assertEqual(self.agent.sleep_min,60*2)
        asyncio.run(run_test())
    
    def test_error_log(self):
        with self.assertLogs(level='ERROR') as captured:
            self.agent.set_pending_executor_removal(3)
            self.assertEqual(len(captured.records), 1) # check that there is only one log message
        with self.assertLogs(level='ERROR') as captured:
            self.agent.set_pending_executor_path_update("my new name", 0xdeafbeef)
            self.assertEqual(len(captured.records), 1) # check that there is only one log message

    @patch('app.service.file_svc.FileSvc.get_payload_name_from_uuid')
    @patch('app.service.file_svc.FileSvc.__init__')
    def test_replace(self, mock_init, mock_uuid):
        mock_init.return_value = None
        mock_uuid.return_value = 'keylogger', 'keylogger'
        svc = FileSvc()
        # echo #{location}
        self.assertEqual(self.agent.replace(b'ZWNobyAje2xvY2F0aW9ufQ==', svc), "echo C:\\Users\\Public\\sandcat.go-windows.exe")
        # ping #{server}
        self.assertEqual(self.agent.replace(b'cGluZyAje3NlcnZlcn0=', svc), "ping 192.168.1.1")
        # some word
        # with
        # multi line
        # exe name: #{exe_name}
        self.assertEqual(self.agent.replace(b'c29tZSB3b3JkCndpdGgKbXVsdGkgbGluZQpleGUgbmFtZTogI3tleGVfbmFtZX0=', svc), "some wordwithmulti lineexe name: sandcat.go-windows.exe")
        
        #./#{payload:b6aab2a6-67c9-44ee-99d4-e4091ab3ad39}
        self.assertEqual(self.agent.replace(b'Li8je3BheWxvYWQ6YjZhYWIyYTYtNjdjOS00NGVlLTk5ZDQtZTQwOTFhYjNhZDM5fQ==', svc), "./keylogger")
    
    @patch('app.service.data_svc.DataService.locate')
    @patch('app.objects.c_agent.Agent.task')
    def test_bootstrap(self, mock_task, mock_locate):
        svc = DataService()
        mock_locate.return_value = [Ability(ability_id='36eecb80-ede3-442b-8774-956e906aff02', executors=[Executor(name='sh', platform='linux', command='whoami')], privilege='User')]
        mock_task.return_value = None
        self.agent.apply_config(name='agents', config={})
        self.agent.set_config(name='agents', prop='bootstrap_abilities', value=['36eecb80-ede3-442b-8774-956e906aff02'])
        async def run_test(svc):
            await self.agent.bootstrap(svc)
        asyncio.run(run_test(svc))
    
    @patch('app.service.event_svc.EventService.fire_event')
    def test_all_facts(self, mock_fire_event):
        app_config = self.app_config()
        BaseWorld.apply_config(name='main', config=app_config)
        baseService = BaseService()
        knowledge_svc = KnowledgeService()
        cotact_svc = ContactService()
        baseService.add_service('contact_svc', cotact_svc)
        event_svc = EventService()
        baseService.add_service('knowledge_svc', knowledge_svc)
        fact = [Fact(trait='host.user.name', value='test', score=1, collected_by='123', technique_id='123', source='123'),
                Fact(trait='192.168.0.1', value='test2', score=1, collected_by='123', technique_id='123', source='456'),
                Fact(trait='C:/Windows/Temp', value='test3', score=1, collected_by='123', technique_id='123', source='123')]
        mock_fire_event.return_value = None
        async def run_test():
            for i in range(len(fact)):
                await knowledge_svc.add_fact(fact[i])
            result = await self.agent.all_facts()
            self.assertEqual(len(result), 2)
        asyncio.run(run_test())
    
    def app_config(self):
        return {
        'app.contact.dns.domain': 'mycaldera.caldera',
        'app.contact.dns.socket': '0.0.0.0:8853',
        'app.contact.html': '/weather',
        'app.contact.http': '0.0.0.0:8888',
        'app.contact.tcp': '0.0.0.0:7010',
        'app.contact.tunnel.ssh.socket': '0.0.0.0:8022',
        'app.contact.udp': '0.0.0.0:7013',
        'app.contact.websocket': '0.0.0.0:7012',
        'plugins': [
            'stockpile',
            'atomic'
        ],
        'host': '0.0.0.0',
        'auth.login.handler.module': 'default',
        'users': {
            'red': {
                'red': 'password-foo'
            },
            'blue': {
                'blue': 'password-bar'
            }
        }
    }
