import unittest
import mock
import  tarantool
from source import notification_pusher

class NotificationPusherTestCase(unittest.TestCase):
    def test_stop_handler(self):
        notification_pusher.run_application = True
        exit_code = 42
        notification_pusher.stop_handler(exit_code)
        self.assertFalse(notification_pusher.run_application)

    def test_done_with_processed_tasks_succ(self):
        task = mock.Mock()
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(return_value = (task, 'action'))

        m_logger = mock.MagicMock()
        with mock.patch('notification_pusher.logger', m_logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertFalse(m_logger.exception.called)

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

    def test_done_with_processed_tasks_empty_list(self):
        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value = 1)
        task_queue.get_nowait = mock.Mock(side_effect = notification_pusher.gevent_queue.Empty)
        try:
            notification_pusher.done_with_processed_tasks(task_queue)
        except notification_pusher.gevent_queue.Empty:
			self.fail()