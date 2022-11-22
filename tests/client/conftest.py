import os

import pytest

from ai.backend.client.config import APIConfig, set_config


@pytest.fixture(autouse=True)
def defconfig():
    endpoint = os.environ.get('BACKEND_TEST_ENDPOINT', 'http://127.0.0.1:8081')
    access_key = os.environ.get('BACKEND_TEST_ADMIN_ACCESS_KEY',
                                'AKIAIOSFODNN7EXAMPLE')
    secret_key = os.environ.get('BACKEND_TEST_ADMIN_SECRET_KEY',
                                'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')
    c = APIConfig(endpoint=endpoint, access_key=access_key, secret_key=secret_key)
    set_config(c)
    return c


@pytest.fixture
def userconfig():
    endpoint = os.environ.get('BACKEND_TEST_ENDPOINT', 'http://127.0.0.1:8081')
    access_key = os.environ.get('BACKEND_TEST_USER_ACCESS_KEY',
                                'AKIANABBDUSEREXAMPLE')
    secret_key = os.environ.get('BACKEND_TEST_USER_SECRET_KEY',
                                'C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf')
    c = APIConfig(endpoint=endpoint, access_key=access_key, secret_key=secret_key)
    set_config(c)
    return c


@pytest.fixture
def example_keypair(defconfig):
    return (defconfig.access_key, defconfig.secret_key)


@pytest.fixture
def user_keypair(userconfig):
    return (userconfig.access_key, userconfig.secret_key)


@pytest.fixture
def dummy_endpoint(defconfig):
    return str(defconfig.endpoint) + '/'
