import unittest
import mock
import tarantool
import json
from source import notification_pusher

def stop_notification_pusher(*smth):
    notification_pusher.run_application = False

def start_notification_pusher(*smth):
    notification_pusher.run_application = True

class NotificationPusherTestCase(unittest.TestCase):

    def setUp(self):
		self.config = mock.Mock()
		self.config.QUEUE_PORT 	= 42
		self.config.QUEUE_HOST 	= '0.0.0.0'
		self.config.QUEUE_SPACE = 0
		self.config.QUEUE_TAKE_TIMEOUT = 0
		self.config.WORKER_POOL_SIZE = 1
		self.config.SLEEP = 0
		self.config.QUEUE_TUBE = 'tube'

    def test_stop_handler(self):
        notification_pusher.run_application = True
        notification_pusher.stop_handler(notification_pusher.exit_code)
        self.assertFalse(notification_pusher.run_application)

    def test_done_with_processed_tasks_suc(self):
        task = mock.Mock()
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value = (task, 'action'))
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

    def test_mainloop_conf_succ(self):
        task_queue = mock.Mock(side_effect = stop_notification_pusher)
        task_done = mock.MagicMock()
        with mock.patch('gevent.queue.Queue', task_queue), mock.patch('notification_pusher.done_with_processed_tasks', task_done):
            notification_pusher.main_loop(self.config)
        task_done.assert_called_once()

    def test_mainloop_worker_fail(self):
        taker = mock.MagicMock()
        with mock.patch('tarantool_queue.tarantool_queue.Tube.take', taker):
            with mock.patch('notification_pusher.sleep', mock.Mock(side_effect=stop_notification_pusher)):
                notification_pusher.main_loop(self.config)
        self.assertFalse(taker.called)

    def test_mainloop_worker_succ(self):
        worker = mock.Mock()
        with mock.patch('gevent.Greenlet', mock.Mock(return_value=worker)):
            with mock.patch('notification_pusher.sleep', mock.Mock(side_effect=stop_notification_pusher)):
                notification_pusher.main_loop(self.config)
        worker.start.assert_called_once()

    def test_mainloop_app_no_run(self):
        m_logger_info = mock.MagicMock()
        notification_pusher.run_application = False
        with mock.patch('notification_pusher.logger.info', m_logger_info):
            notification_pusher.main_loop(self.config)
        m_logger_info.assert_called_with('Stop application loop.')
        notification_pusher.run_application = True

    def test_install_signal_handlers(self):
        with mock.patch('gevent.signal', mock.Mock()) as signal:
            notification_pusher.install_signal_handlers()
        assert signal.called


