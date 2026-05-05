import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: hits real FilmAffinity site (requires network)")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration", default=False):
        skip = pytest.mark.skip(reason="pass --integration to run")
        for item in items:
            if item.get_closest_marker("integration"):
                item.add_marker(skip)


def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", default=False)
