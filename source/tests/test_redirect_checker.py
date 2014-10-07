import mock
import unittest
from source import redirect_checker
from argparse import Namespace

def stop_redirect_checker(*smth):
    redirect_checker.isRunning = False


def start_redirect_checker(*smth):
    redirect_checker.isRunning = True

class RedirectCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = mock.Mock()
        self.config.WORKER_POOL_SIZE = 42
        self.config.SLEEP = 1
        self.config.CHECK_URL = "url"
        self.config.HTTP_TIMEOUT = 20
        redirect_checker.sleep = mock.Mock(side_effect=stop_redirect_checker)

    def test_main_loop_with_network_and_normal_worker_counts(self):
        pid = 42
        children_mock = mock.Mock()
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as workd:
                        redirect_checker.main_loop(self.config)
        assert workd.called

    def test_main_loop_with_network_status_fail(self):
        pid = 42
        children_mock = mock.Mock()
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=False)):
                    redirect_checker.main_loop(self.config)
        assert children_mock.terminate.called

    def test_main_loop_with_network_and_not_normal_worker_counts(self):
        pid = 42
        children_mock = mock.Mock()
        setattr(self.config, "WORKER_POOL_SIZE", 0)
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[children_mock])):
                with mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)):
                    with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as workd:
                        redirect_checker.main_loop(self.config)

        assert not workd.called

    



    def tearDown(self):
        start_redirect_checker()