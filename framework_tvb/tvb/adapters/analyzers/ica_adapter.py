# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2020, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Adapter that uses the traits module to generate interfaces for ICA Analyzer.

.. moduleauthor:: Paula Sanz Leon

"""

import uuid
import numpy
from tvb.adapters.datatypes.db.mode_decompositions import IndependentComponentsIndex
from tvb.adapters.datatypes.db.time_series import TimeSeriesIndex
from tvb.adapters.datatypes.h5.mode_decompositions_h5 import IndependentComponentsH5
from tvb.analyzers.ica import compute_ica_decomposition
from tvb.core.adapters.abcadapter import ABCAdapterForm, ABCAdapter
from tvb.core.entities.filters.chain import FilterChain
from tvb.core.neocom import h5
from tvb.core.neotraits.forms import TraitDataTypeSelectField, IntField
from tvb.core.neotraits.view_model import ViewModel, DataTypeGidAttr
from tvb.datatypes.time_series import TimeSeries
from tvb.basic.neotraits.api import HasTraits, Attr, Int


class ICAAdapterModel(ViewModel):
    time_series = DataTypeGidAttr(
        linked_datatype=TimeSeries,
        label="Time Series",
        required=True,
        doc="The timeseries to which the ICA is to be applied."
    )

    n_components = Int(
        label="Number of principal components to unmix.",
        required=False,
        default=None,
        doc="Number of principal components to unmix.")


class ICAAdapterForm(ABCAdapterForm):

    def __init__(self, project_id=None):
        super(ICAAdapterForm, self).__init__(project_id)
        self.time_series = TraitDataTypeSelectField(ICAAdapterModel.time_series, self.project_id, name='time_series',
                                                    conditions=self.get_filters(), has_all_option=True)
        self.n_components = IntField(ICAAdapterModel.n_components, self.project_id)
        self.project_id = project_id

    @staticmethod
    def get_view_model():
        return ICAAdapterModel

    @staticmethod
    def get_required_datatype():
        return TimeSeriesIndex

    @staticmethod
    def get_filters():
        return FilterChain(fields=[FilterChain.datatype + '.data_ndim'], operations=["=="], values=[4])

    @staticmethod
    def get_input_name():
        return "time_series"


class ICAAdapter(ABCAdapter):
    """ TVB adapter for calling the ICA algorithm. """

    _ui_name = "Independent Component Analysis"
    _ui_description = "ICA for a TimeSeries input DataType."
    _ui_subsection = "ica"

    def get_form_class(self):
        return ICAAdapterForm

    def get_output(self):
        return [IndependentComponentsIndex]

    def configure(self, view_model):
        # type: (ICAAdapterModel) -> None
        """
        Store the input shape to be later used to estimate memory usage. Also
        create the algorithm instance.
        """
        self.input_time_series_index = self.load_entity_by_gid(view_model.time_series)
        self.input_shape = (self.input_time_series_index.data_length_1d,
                            self.input_time_series_index.data_length_2d,
                            self.input_time_series_index.data_length_3d,
                            self.input_time_series_index.data_length_4d)
        self.log.debug("Time series shape is %s" % str(self.input_shape))
        self.log.debug("Provided number of components is %s" % view_model.n_components)
        # -------------------- Fill Algorithm for Analysis -------------------##
        if view_model.n_components is None:
            view_model.n_components = self.input_time_series_index.data_length_3d

    def get_required_memory_size(self, view_model):
        # type: (ICAAdapterModel) -> int
        """
        Return the required memory to run this algorithm.
        """
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        input_size = numpy.prod(used_shape) * 8.0
        output_size = self.result_size(self.input_shape, view_model.n_components)
        return input_size + output_size

    def get_required_disk_size(self, view_model):
        # type: (ICAAdapterModel) -> int
        """
        Returns the required disk size to be able to run the adapter (in kB).
        """
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        return self.array_size2kb(self.result_size(used_shape, view_model.n_components))

    def launch(self, view_model):
        # type: (ICAAdapterModel) -> [IndependentComponentsIndex]
        """
        :param view_model: the ViewModel keeping the algorithm inputs
        :return: the ica index for the specified time series
        Launch algorithm and build results. 
        """
        # --------- Prepare a IndependentComponents object for result ----------##
        ica_index = IndependentComponentsIndex()
        time_series_h5 = h5.h5_file_for_index(self.input_time_series_index)

        result_path = h5.path_for(self.storage_path, IndependentComponentsH5, ica_index.gid)
        ica_h5 = IndependentComponentsH5(path=result_path)

        # ------------- NOTE: Assumes 4D, Simulator timeSeries. --------------##
        input_shape = time_series_h5.data.shape
        node_slice = [slice(input_shape[0]), None, slice(input_shape[2]), slice(input_shape[3])]

        # ---------- Iterate over slices and compose final result ------------##
        small_ts = TimeSeries()
        for var in range(input_shape[1]):
            node_slice[1] = slice(var, var + 1)
            small_ts.data = time_series_h5.read_data_slice(tuple(node_slice))
            partial_ica = compute_ica_decomposition(small_ts, view_model.n_components)
            ica_h5.write_data_slice(partial_ica)

        partial_ica.source.gid = view_model.time_series
        partial_ica.gid = uuid.UUID(ica_index.gid)

        ica_index.fill_from_has_traits(partial_ica)
        ica_h5.close()
        time_series_h5.close()

        return ica_index

    @staticmethod
    def result_shape(input_shape, n_components):
        """Returns the shape of the mixing matrix."""
        n = n_components or input_shape[2]
        return n, n, input_shape[1], input_shape[3]

    def result_size(self, input_shape, n_components):
        """Returns the storage size in bytes of the mixing matrix of the ICA analysis, assuming 64-bit float."""
        return numpy.prod(self.result_shape(input_shape, n_components)) * 8
