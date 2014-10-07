import unittest
import mock
import source.lib.worker as worker
from tarantool.error import DatabaseError


class WorkerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_with_error(self):
        timeout = "timeout"
        url = "url"
        history_types = ["ERROR"]
        history_urls = ["url"]
        counters = ["counter"]
        history_retrun = (history_types, history_urls, counters)

        url = "url"
        url_id = "url_id"
        recheck = "recheck"
        task_mock = mock.Mock()
        task_mock.data = {url: url, url_id: url_id, recheck: False}

        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=history_retrun)):
                result = worker.get_redirect_history_from_task(task_mock, timeout)
        self.assertEqual(result, (True, {url: url, url_id: url_id, recheck: True}))
        pass
    def test_get_redirect_history_from_task_ok(self):
        timeout = "timeout"
        url = "url"
        history_types = ["type"]
        history_urls = ["url"]
        counters = ["counter"]
        history_retrun = (history_types, history_urls, counters)

        url = "url"
        url_id = "url_id"
        recheck = "recheck"
        task_mock = mock.Mock()
        task_mock.data = {url: url, url_id: url_id, recheck: True}

        data = {
            "url_id": task_mock.data["url_id"],
            "result": [history_types, history_urls, counters],
            "check_type": "normal"
        }
        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=history_retrun)):
                result = worker.get_redirect_history_from_task(task_mock, timeout)
        self.assertEqual(result, (False, data))
        pass
    def test_get_redirect_history_from_task_suspicious(self):
        timeout = "timeout"
        url = "url"
        history_types = ["type"]
        history_urls = ["url"]
        counters = ["counter"]
        history_retrun = (history_types, history_urls, counters)

        url = "url"
        url_id = "url_id"
        recheck = "recheck"
        suspicious = "suspicious"
        task_mock = mock.Mock()
        task_mock.data = {url: url, url_id: url_id, recheck: True, suspicious: suspicious}

        data = {
            "url_id": task_mock.data["url_id"],
            "result": [history_types, history_urls, counters],
            "check_type": "normal",
            "suspicious": task_mock.data['suspicious']
        }
        with mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value=url)):
            with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=history_retrun)):
                result = worker.get_redirect_history_from_task(task_mock, timeout)
        self.assertEqual(result, (False, data))
        pass

    def test_worker_with_no_task(self):
        config = mock.Mock()
        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=None)
        output_tube = mock.MagicMock()
        parent_pid = 12345

        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', mock.Mock()):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock()) as history:
                        worker.worker(config, parent_pid)
        self.assertEqual(history.call_count, 0)
        pass
    def test_worker_with_task_with_result_with_no_input(self):
        config = mock.Mock()

        task = mock.MagicMock()
        task.task_id = 123

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)

        output_tube = mock.MagicMock()
        output_tube.put = mock.Mock()

        parent_pid = 12345

        is_input = False
        data = "data"
        history = (is_input, data)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', mock.Mock()):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=history)):
                        worker.worker(config, parent_pid)
        output_tube.put.assert_called_once_with(data)
        pass
    def test_worker_with_task_with_result_with_input(self):
        config = mock.Mock()

        task = mock.MagicMock()
        task.task_id = 123

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)
        input_tube.put = mock.Mock()

        output_tube = mock.MagicMock()

        parent_pid = 12345

        is_input = True
        data = "data"
        history = (is_input, data)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', mock.Mock()):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=history)):
                        worker.worker(config, parent_pid)
        self.assertEqual(input_tube.put.call_count, 1)
        pass
    def test_worker_with_task_with_no_result(self):
        config = mock.Mock()

        task = mock.MagicMock()
        task.task_id = 123

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)

        output_tube = mock.MagicMock()

        parent_pid = 12345

        logger = mock.Mock()
        logger.debug = mock.Mock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', logger):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None)):
                        worker.worker(config, parent_pid)
        self.assertEqual(logger.debug.call_count, 0)
        pass
    def test_worker_with_task_with_no_result_exeption(self):
        config = mock.Mock()

        exeption = DatabaseError("test exeption")

        task = mock.MagicMock()
        task.task_id = 123
        task.ack = mock.Mock(side_effect=exeption)

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)

        output_tube = mock.MagicMock()

        parent_pid = 12345

        logger = mock.Mock()
        logger.exeption = mock.Mock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', logger):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None)):
                        worker.worker(config, parent_pid)
        logger.exception.assert_called_once_with(exeption)
        pass
    