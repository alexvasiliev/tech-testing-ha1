import unittest
import mock
import source.lib.worker as worker


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
        print "test_worker_with_no_task"
        config = mock.Mock()
        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=None)
        output_tube = mock.MagicMock()
        parent_pid = 12345
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', mock.Mock()):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    worker.worker(config, parent_pid)
        print "test_worker_with_no_task ended"
        pass

    """
    def test_worker(self):
        config = mock.Mock()
        input_tube = mock.MagicMock()
        task = {"task_id":123}
        input_tube.take = mock.Mock(return_value=task)
        output_tube = mock.MagicMock()
        parent_pid = 12345
        with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            with mock.patch('source.lib.worker.logger', mock.Mock()):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                    worker.worker(config, parent_pid)

        pass
    """