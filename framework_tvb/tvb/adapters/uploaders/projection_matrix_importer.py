# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2017, Baycrest Centre for Geriatric Care ("Baycrest") and others
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
.. moduleauthor:: Marmaduke Woodman <marmaduke.woodman@univ-amu.fr>
.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.exceptions import LaunchException
from tvb.core.adapters.abcuploader import ABCUploader, ABCUploaderForm
from tvb.core.entities.filters.chain import FilterChain
from tvb.adapters.datatypes.db.projections import ProjectionMatrixIndex
from tvb.adapters.datatypes.db.sensors import SensorsIndex
from tvb.core.neotraits.forms import TraitUploadField, StrField, TraitDataTypeSelectField
from tvb.core.neocom import h5
from tvb.core.neotraits.view_model import ViewModel, UploadAttr, DataTypeGidAttr
from tvb.datatypes.sensors import SensorsEEG, SensorsMEG, Sensors
from tvb.datatypes.projections import *
from tvb.datatypes.surfaces import CorticalSurface, Surface

DEFAULT_DATASET_NAME = "ProjectionMatrix"


def determine_projection_type(sensors_idx):
    # type: (SensorsIndex) -> str
    if sensors_idx.sensors_type == SensorsEEG.sensors_type.default:
        projection_matrix_type = ProjectionSurfaceEEG.projection_type.default
    elif sensors_idx.sensors_type == SensorsMEG.sensors_type.default:
        projection_matrix_type = ProjectionSurfaceMEG.projection_type.default
    else:
        projection_matrix_type = ProjectionSurfaceSEEG.projection_type.default

    return projection_matrix_type


class ProjectionMatrixImporterModel(ViewModel):
    projection_file = UploadAttr(
        field_type=str,
        label='Projection matrix file (.mat or .npy format)',
        doc='Expected a file containing projection matrix (one vector of length '
            'number of surface vertices nd values in the sensors range).'
    )

    dataset_name = Attr(
        field_type=str,
        required=False,
        default=DEFAULT_DATASET_NAME,
        label='Matlab dataset name',
        doc='Name of the MATLAB dataset where data is stored. Required only for .mat files'
    )

    surface = DataTypeGidAttr(
        linked_datatype=Surface,
        label='Brain Cortical Surface',
        doc='The Brain Surface used by the uploaded projection matrix.'
    )

    sensors = DataTypeGidAttr(
        linked_datatype=Sensors,
        label='Sensors',
        doc='The Sensors used in for current projection.'
    )


class ProjectionMatrixImporterForm(ABCUploaderForm):

    def __init__(self, prefix='', project_id=None):
        super(ProjectionMatrixImporterForm, self).__init__(prefix, project_id)
        self.projection_file = TraitUploadField(ProjectionMatrixImporterModel.projection_file, '.mat, .npy', self,
                                                name='projection_file')
        self.dataset_name = StrField(ProjectionMatrixImporterModel.dataset_name, self, name='dataset_name')
        surface_conditions = FilterChain(fields=[FilterChain.datatype + '.surface_type'], operations=['=='],
                                         values=['Cortical Surface'])
        self.surface = TraitDataTypeSelectField(ProjectionMatrixImporterModel.surface, self, name='surface',
                                                conditions=surface_conditions)
        self.sensors = TraitDataTypeSelectField(ProjectionMatrixImporterModel.sensors, self, name='sensors')

    @staticmethod
    def get_view_model():
        return ProjectionMatrixImporterModel


class ProjectionMatrixSurfaceEEGImporter(ABCUploader):
    """
    Upload ProjectionMatrix Cortical Surface -> EEG/MEG/SEEG Sensors from a MAT or NPY file.
    """

    _ui_name = "Gain Matrix for Sensors"
    _ui_description = "Upload a Projection Matrix between a Brain Cortical Surface and EEG/MEG Sensors."
    logger = get_logger(__name__)

    def get_form_class(self):
        return ProjectionMatrixImporterForm

    def get_output(self):
        return [ProjectionMatrixIndex]

    def launch(self, view_model):
        # type: (ProjectionMatrixImporterModel) -> [ProjectionMatrixIndex]
        """
        Creates ProjectionMatrix entity from uploaded data.

        :raises LaunchException: when
                    * no projection_file or sensors are specified
                    * the dataset is invalid
                    * number of sensors is different from the one in dataset
        """
        if view_model.projection_file is None:
            raise LaunchException("Please select MATLAB file which contains data to import")

        if sensors is None:
            raise LaunchException("No sensors selected. Please initiate upload again and select one.")

        if view_model.surface is None:
            raise LaunchException("No source selected. Please initiate upload again and select a source.")

        surface_index = self.load_entity_by_gid(view_model.surface.hex)
        expected_shape = surface_index.number_of_vertices

        self.logger.debug("Reading projection matrix from uploaded file...")
        if view_model.projection_file.endswith(".mat"):
            projection_data = self.read_matlab_data(view_model.projection_file, view_model.dataset_name)
        else:
            projection_data = self.read_list_data(view_model.projection_file)

        if projection_data is None or len(projection_data) == 0:
            raise LaunchException("Invalid (empty) dataset...")

        if projection_data.shape[0] != sensors.number_of_sensors:
            raise LaunchException("Invalid Projection Matrix shape[0]: %d Expected: %d" % (projection_data.shape[0],
                                                                                           sensors.number_of_sensors))

        if projection_data.shape[1] != expected_shape:
            raise LaunchException("Invalid Projection Matrix shape[1]: %d Expected: %d" % (projection_data.shape[1],
                                                                                           expected_shape))

        projection_matrix_type = determine_projection_type(sensors)
        surface_ht = h5.load_from_index(surface_index, CorticalSurface)
        sensors_ht = h5.load_from_index(sensors)
        projection_matrix = ProjectionMatrix(sources=surface_ht, sensors=sensors_ht,
                                             projection_type=projection_matrix_type,
                                             projection_data=projection_data)
        return h5.store_complete(projection_matrix, self.storage_path)
