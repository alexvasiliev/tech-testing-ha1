import unittest
import mock
import source.lib.utils as utils
import argparse
import tarantool_queue


class UtilsTestCase(unittest.TestCase):
    def test_daemonize_parent(self):
        pid = 12345
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize();
        self.assertEqual(os_fork.call_count, 1)
        os_exit.assert_called_once_with(0)
        self.assertEqual(os_setsid.call_count, 0)
        pass

    def test_daemonize_child(self):
        pid = 12345
        with mock.patch('os.fork', mock.Mock(side_effect=[0,pid])) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize();
        os_exit.assert_called_once_with(0)
        self.assertEqual(os_fork.call_count, 2)
        self.assertEqual(os_setsid.call_count, 1)
        pass

    def test_daemonize_child_child(self):
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    utils.daemonize();
        self.assertEqual(os_fork.call_count, 2)
        self.assertEqual(os_exit.call_count, 0)
        self.assertEqual(os_setsid.call_count, 1)
        pass

    def test_daemonize_exeption(self):
        exception = OSError("test_exeption")
        with mock.patch('os.fork', mock.Mock(side_effect=exception)) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    self.assertRaises(Exception, utils.daemonize)
        self.assertEqual(os_fork.call_count, 1)
        self.assertEqual(os_exit.call_count, 0)
        self.assertEqual(os_setsid.call_count, 0)
        pass

    def test_daemonize_child_exeption(self):
        exception = OSError("test_exeption")
        with mock.patch('os.fork', mock.Mock(side_effect=[0,exception])) as os_fork:
            with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                with mock.patch('os._exit', mock.Mock()) as os_exit:
                    self.assertRaises(Exception, utils.daemonize)
        self.assertEqual(os_fork.call_count, 2)
        self.assertEqual(os_exit.call_count, 0)
        self.assertEqual(os_setsid.call_count, 1)
        pass

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        test_path = 'test_path'
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile(test_path)
        m_open.assert_called_once_with(test_path, 'w')
        m_open().write.assert_called_once_with(str(pid))
        pass

    def test_load_config_from_pyfile(self):
        test_file_data = {
            'QWE': '123',
            'asd': '456',
            'ZXC0': {'zxc', '789'}
        }
        test_path = 'test_path'
        with mock.patch('source.lib.utils.load_config_from_pyfile_execfile', mock.Mock(return_value=test_file_data)) as exec_py:
            variables = test_file_data
            result = utils.load_config_from_pyfile(test_path)

        exec_py.assert_called_once_with(test_path)
        self.assertEqual(result.QWE, test_file_data['QWE'])
        self.assertEqual(result.ZXC0, test_file_data['ZXC0'])
        self.assertRaises(AttributeError, lambda: result.asd)
        pass

    def test_parse_cmd_args(self):
        description = "description"
        descr = 'test_app'
        test_path = 'test_path'
        pid = str(12345)
        
        args = ["-c", test_path]
        result = utils.parse_cmd_args(args, description)
        self.assertEqual(result, argparse.Namespace(config=test_path, daemon=False, pidfile=None))
        
        args = ["-c", test_path, "-d"]
        result = utils.parse_cmd_args(args, description)
        self.assertEqual(result, argparse.Namespace(config=test_path, daemon=True, pidfile=None))
        
        args = ["-c", test_path,"-P", pid]
        result = utils.parse_cmd_args(args, description)
        self.assertEqual(result, argparse.Namespace(config=test_path, daemon=False, pidfile=pid))
        
        args = ["-c", test_path, "-d", "-P", pid]
        result = utils.parse_cmd_args(args, description)
        self.assertEqual(result, argparse.Namespace(config=test_path, daemon=True, pidfile=pid))
        pass

    def test_get_tube(self):
        host = "Host"
        port = "Port"
        space = "Space"
        name = "Name"
        innerMock = mock.Mock()
        innerMock.tube = mock.Mock()
        with mock.patch('tarantool_queue.tarantool_queue.Queue', mock.Mock(return_value=innerMock)) as queue:
            result = utils.get_tube(host, port, space, name)
        queue.assert_called_once_with(host=host, port=port, space=space)
        innerMock.tube.assert_called_once_with(name)
        pass

    def test_spawn_workers(self):
        num = 12
        target = "target"
        args = "args"
        parent_pid = "parent_pid"
        innerMock = mock.Mock()
        innerMock.start = mock.Mock()
        with mock.patch('source.lib.utils.Process', mock.Mock(return_value=innerMock)) as process:
            utils.spawn_workers(num, target, args, parent_pid)
        self.assertEqual(process.call_count, num)
        self.assertEqual(innerMock.start.call_count, num)
        pass

    def test_spawn_zero_workers(self):
        num = 0
        target = "target"
        args = "args"
        parent_pid = "parent_pid"
        innerMock = mock.Mock()
        innerMock.start = mock.Mock()
        with mock.patch('source.lib.utils.Process', mock.Mock(return_value=innerMock)) as process:
            utils.spawn_workers(num, target, args, parent_pid)
        self.assertEqual(process.call_count, num)
        self.assertEqual(innerMock.start.call_count, num)
        pass

    def test_check_network_status(self):
        check_url = "check_url"
        timeout = "timeout"
        with mock.patch('urllib2.urlopen', mock.Mock()):
            result = utils.check_network_status(check_url, timeout)
        self.assertTrue(result)
        pass

    def test_check_network_status_exeption(self):
        check_url = "check_url"
        timeout = "timeout"
        exception = ValueError("test_exeption")
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=exception)):
            self.assertRaises(Exception, utils.check_network_status)
        pass