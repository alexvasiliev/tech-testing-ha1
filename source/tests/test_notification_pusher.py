import unittest
import mock
import tarantool
import tarantool_queue
import json
from source import notification_pusher
from argparse import Namespace

def stop_notification_pusher(*smth):
    notification_pusher.run_application = False

def start_notification_pusher(*smth):
    notification_pusher.run_application = True



class NotificationPusherTestCase(unittest.TestCase):

    def setUp(self):
        self.config = mock.Mock()
        self.config.QUEUE_PORT 	= 42
        self.config.QUEUE_HOST 	= '0.0.0.0'
        self.config.WORKER_POOL_SIZE = 1
        self.config.QUEUE_SPACE  = 0
        notification_pusher.logger = mock.MagicMock()


    def test_stop_handler(self):
        notification_pusher.stop_handler(notification_pusher.exit_code)
        self.assertFalse(notification_pusher.run_application)

    def test_done_with_processed_tasks_suc(self):
        task = mock.Mock()
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value = (task, 'task_method'))
        logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertFalse(logger.exception.called)

    def test_done_with_processed_tasks_err(self):
        task = mock.Mock()
        task.task_method = mock.Mock(side_effect=tarantool.DatabaseError())
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value=(task, 'task_method'))
        try:
            notification_pusher.done_with_processed_tasks(task_queue)
        except tarantool.DatabaseError:
            self.fail()

    def test_done_with_processed_tasks_empty(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(side_effect = notification_pusher.gevent_queue.Empty)
        mock.patch('source.notification_pusher.logger.debug', mock.Mock())
        try:
            notification_pusher.done_with_processed_tasks(task_queue)
        except notification_pusher.gevent_queue.Empty:
			self.fail()

    def test_notification_worker_ack(self):
        data = {'callback_url': 'url'}
        task = mock.Mock()
        task.data.copy = mock.Mock(return_value=data)
        task_queue = mock.MagicMock()
        response = mock.Mock(return_value={'status_code': 200})
        with mock.patch.object(json, 'dumps', mock.Mock()), mock.patch('source.notification_pusher.requests.post',
                           mock.Mock(return_value=response)):
            notification_pusher.notification_worker(task, task_queue)
        task_queue.put.assert_called_with((task, 'ack'))

    def test_notification_worker_bury(self):
        data = {'callback_url': 'url'}
        task = mock.Mock()
        task.data.copy = mock.Mock(return_value=data)
        task_queue = mock.MagicMock()
        with mock.patch.object(json, 'dumps', mock.Mock()), mock.patch('source.notification_pusher.requests.post',
                           mock.Mock(side_effect=notification_pusher.requests.RequestException("exc"))):
            notification_pusher.notification_worker(task, task_queue)
        task_queue.put.assert_called_with((task, 'bury'))

    def test_install_signal_handlers(self):
        with mock.patch('gevent.signal', mock.Mock()) as signal:
            notification_pusher.install_signal_handlers()
        assert signal.called

    def test_main_loop_no_task(self):
        queue = mock.Mock(name="queue")
        queue.tube().take = mock.Mock(return_value=None)
        tarantool_queue.Queue = mock.Mock(return_value=queue)

        with mock.patch('source.notification_pusher.sleep', stop_notification_pusher),\
             mock.patch('source.notification_pusher.Greenlet', mock.Mock()) as creation:
            notification_pusher.main_loop(self.config)

        assert not creation.called

    def test_main(self):
        setattr(self.config, "LOGGING", {"version": 1})
        notification_pusher.parse_cmd_args = mock.Mock()
        notification_pusher.parse_cmd_args.return_value = Namespace(daemon=False, config='config', pidfile=False)
        with mock.patch('source.notification_pusher.main_loop', mock.Mock(side_effect=stop_notification_pusher)) as main_loop, \
             mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)),\
             mock.patch('source.notification_pusher.install_signal_handlers', mock.Mock()),\
             mock.patch('source.notification_pusher.patch_all', mock.Mock()):
                notification_pusher.main([])

        main_loop.assert_called_once_with(self.config)

    def test_main_with_pidfile(self):
        setattr(self.config, "LOGGING", {"version": 1})
        notification_pusher.parse_cmd_args = mock.Mock()
        stop_notification_pusher();
        notification_pusher.parse_cmd_args.return_value = Namespace(daemon=False, config='config', pidfile=True)
        with mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)), \
                mock.patch('source.notification_pusher.create_pidfile', mock.Mock()) as create_pidfile,\
                mock.patch('source.notification_pusher.install_signal_handlers', mock.Mock()),\
                mock.patch('source.notification_pusher.patch_all', mock.Mock()):
                notification_pusher.main([])
        assert create_pidfile.called

    def test_main_with_daemonize(self):
        setattr(self.config, "LOGGING", {"version": 1})
        stop_notification_pusher();
        notification_pusher.parse_cmd_args.return_value = Namespace(daemon=True, config='config', pidfile=False)
        with mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)), \
             mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize,\
             mock.patch('source.notification_pusher.install_signal_handlers', mock.Mock()),\
             mock.patch('source.notification_pusher.patch_all', mock.Mock()):
                notification_pusher.main([])

        assert daemonize.called

    def tearDown(self):
        start_notification_pusher()