# Copyright 2019 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the :mod:`pennylane.circuit_graph` module.
"""
# pylint: disable=no-self-use,too-many-arguments,protected-access

import pytest

import pennylane as qml


class TestPennyLaneInit:
    """Unit tests for the functions in the pennylane/__init__.py."""

    def test_plugin_converters(self, monkeypatch):
        """Test that the load function returns a callable function using entrypoints."""
        import pkg_resources
        import importlib

        class DummyModule:

            def some_load_function(*args):
                def some_callable_function():
                    return
                return some_callable_function
        with monkeypatch.context() as m:
            new_plugin_converters = qml.plugin_converters
            ep = pkg_resources.EntryPoint.parse('some_load_function = dummy_module:some_load_function')
            new_plugin_converters['pennylane.io'] = {'dummy': ep}

            m.setattr('pennylane.plugin_converters', new_plugin_converters)

            assert 'some_load_function' in qml.plugin_converters
            assert callable(qml.load(None, format='some_load_function'))

    def test_plugin_converters_error(self):
        """Test that the load function returns an error given invalid arguments."""

        with pytest.raises(ValueError, match="Converter does not exist. "
                                             "Make sure the required plugin is installed "
                                             "and supports conversion."):
            qml.load(None, format='some_load_function')
