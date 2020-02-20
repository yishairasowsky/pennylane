# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

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
This module contains the :class:`VariableRef` class, which is used to track
and identify :class:`~pennylane.qnode.QNode` parameters.

Description
-----------

The first time a QNode is evaluated (either by calling :meth:`~.QNode.evaluate`,
:meth:`~.QNode.__call__`, or :meth:`~.QNode.jacobian`), the :meth:`~.QNode.construct`
method is called, which performs a 'just-in-time' circuit construction
on the :mod:`~pennylane._device.Device`. As part of this construction, all arguments
and keyword arguments are wrapped in a `VariableRef` as follows:

* All positional arguments in ``*args``, including those with multiple dimensions, are
  flattened to a single list, and each element wrapped as a VariableRef instance,
  indexed by its position in the list.

  This allows PennyLane to inspect the shape and type of arguments
  the user wishes to pass. The list can then be unflattened back to the original
  shape of ``*args``.


* The same is done for each keyword argument in ``**kwargs``, the only
  difference being that the name of each contained VariableRef corresponds
  with the keyword name.

As a result, the device stores a list of operations and expectations, with all
free parameters stored as VariableRef instances.

.. note::
    The QNode can be differentiated with respect to positional arguments,
    but *not* with respect to keyword arguments. This makes keyword arguments
    a natural location for data placeholders.

.. important::
    If the user defines a keyword argument, then they always have to pass the
    corresponding variable as a keyword argument, otherwise it won't register.

For each successive QNode execution, the user-provided values for the positional and keyword
arguments are stored in :attr:`VariableRef.positional_arg_values` and
:attr:`VariableRef.kwarg_values` respectively; the values are
then returned by :meth:`VariableRef.val`, using the VariableRef's ``idx`` attribute, and, for
keyword arguments, its ``name``, to return the correct value to the operation.

.. note::
    The :meth:`Operation.parameters() <pennylane.operation.Operation.parameters>`
    property automates the process of unpacking the VariableRef value.
    The attribute :meth:`VariableRef.val` should not need to be accessed outside of advanced usage.
"""
import copy


class VariableRef:
    """A reference to dynamically track and update circuit parameters.

    Represents an atomic ("scalar") quantum circuit parameter (with a non-fixed value),
    or data placeholder.

    Each time the circuit is executed, it is given a vector of flattened positional argument values,
    and a dictionary mapping auxiliary argument names to vectors of their flattened values.
    Each element of these vectors corresponds to a VariableRef instance.
    :attr:`VariableRef.idx` is an index into the argument value vector.

    The VariableRef has an optional scalar multiplier for the argument it represents.

    .. note:: VariableRefs currently do not implement any arithmetic
        operations other than scalar multiplication.

    Args:
        idx  (int): index into the value vector, >= 0
        name (str): structured name of the parameter
        basename (None, str): for auxiliary parameters the name of the base parameter, otherwise None
    """

    # pylint: disable=too-few-public-methods

    #: array[float]: current positional parameter values, set in :meth:`.BaseQNode._set_variables`
    positional_arg_values = None

    #: dict[str->array[float]]: current auxiliary parameter values, set in :meth:`.BaseQNode._set_variables`
    kwarg_values = None

    def __init__(self, idx, name=None, basename=None):
        self.idx = idx  #: int: parameter index
        self.name = name  #: str: parameter structured name
        self.basename = basename
        """str, None: for auxiliary parameters the key for the kwarg_values dict"""
        self.mult = 1  #: int, float: parameter scalar multiplier

    def __repr__(self):
        temp = " * {}".format(self.mult) if self.mult != 1.0 else ""
        return "<VariableRef({}:{}{})>".format(self.name, self.idx, temp)

    def __str__(self):
        temp = ", * {}".format(self.mult) if self.mult != 1.0 else ""
        return "VariableRef: name = {}, idx = {}{}".format(self.name, self.idx, temp)

    def __eq__(self, other):
        if not isinstance(other, VariableRef):
            return False

        return (
            self.name == other.name
            and self.idx == other.idx
            and self.is_kwarg == other.is_kwarg
            and self.mult == other.mult
        )

    def __neg__(self):
        """Unary negation."""
        temp = copy.copy(self)
        temp.mult = -temp.mult
        return temp

    def __mul__(self, scalar):
        """Right multiplication by scalars."""
        temp = copy.copy(self)
        temp.mult *= scalar
        return temp

    def __truediv__(self, scalar):
        """Right division by scalars. Left division is not allowed."""
        temp = copy.copy(self)
        temp.mult /= scalar
        return temp

    __rmul__ = __mul__  # Left multiplication by scalars.

    @property
    def is_kwarg(self):
        """Type of the parameter the VariableRef represents.

        Returns:
            bool: True iff the VariableRef represents (an element of) an auxiliary parameter
        """
        return self.basename is not None

    @property
    def val(self):
        """Current numerical value of the VariableRef.

        Returns:
            float: current value of the VariableRef
        """
        # pylint: disable=unsubscriptable-object
        if not self.is_kwarg:
            # The variable is a placeholder for a positional argument
            return VariableRef.positional_arg_values[self.idx] * self.mult

        # The variable is a placeholder for a keyword argument
        values = VariableRef.kwarg_values[self.basename]
        return values[self.idx] * self.mult

    def render(self, show_name_only=False):
        """String representation of the VariableRef for CircuitDrawer.

        Args:
            show_name_only (bool, optional): Render the name instead of the value.

        Returns:
            str: string representation of the VariableRef
        """
        if not show_name_only:
            return str(round(self.val, 3))

        if self.mult != 1:
            return "{}*{}".format(str(round(self.mult, 3)), self.name)

        return self.name
