# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2022, Baycrest Centre for Geriatric Care ("Baycrest") and others
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
# CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
# Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
# Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
# The Virtual Brain: a simulator of primate brain network dynamics.
# Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#
import bct

from tvb.core.entities.model.model_operation import AlgorithmTransientGroup
from tvb.adapters.analyzers.bct_adapters import BaseBCT, bct_description, BaseBCTForm

BCT_GROUP_DEGREE = AlgorithmTransientGroup("Degree and Similarity Algorithms",
                                           "Brain Connectivity Toolbox", "bctdegree")
BCT_GROUP_DENSITY = AlgorithmTransientGroup("Density Algorithms", "Brain Connectivity Toolbox", "bctdensity")


class Degree(BaseBCT):
    """
    """
    _ui_group = BCT_GROUP_DEGREE

    _ui_name = "Degree: Undirected (binary/weighted) connection matrix"
    _ui_description = bct_description("degrees_und.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = {'deg': bct.degrees_und(connectivity.weights)}
        measure_index = self.build_connectivity_measure(result, 'deg', connectivity, "Node degree")
        return [measure_index]


class DegreeIOD(Degree):
    """
    """

    _ui_name = "Indegree and outdegree: Directed (binary/weighted) connection matrix"
    _ui_description = bct_description("degrees_dir.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.degrees_dir(connectivity.weights)
        result = {
            'id': result[0],
            'od': result[1],
            'deg': result[2]
        }
        measure_index1 = self.build_connectivity_measure(result, 'id', connectivity, "Node indegree")
        measure_index2 = self.build_connectivity_measure(result, 'od', connectivity, "Node outdegree")
        measure_index3 = self.build_connectivity_measure(result, 'deg', connectivity,
                                                         "Node degree (indegree + outdegree)")
        return [measure_index1, measure_index2, measure_index3]


class JointDegree(Degree):
    """
    """
    _ui_name = "Joint Degree"
    _ui_description = bct_description("jdegree.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.jdegree(connectivity.weights)
        result = {
            'J': result[0],
            'J_od': result[1],
            'J_id': result[2],
            'J_bl': result[3]
        }
        measure_index = self.build_connectivity_measure(result, 'J', connectivity,
                                                        "Joint Degree JOD=" + str(result['J_od']) +
                                                        ", JID=" + str(result['J_id']) +
                                                        ", JBL=" + str(result['J_bl']),
                                                        "Connectivity Nodes", "Connectivity Nodes")
        value1 = self.build_int_value_wrapper(result, 'J_od', "Number of vertices with od > id")
        value2 = self.build_int_value_wrapper(result, 'J_id', "Number of vertices with id > od")
        value3 = self.build_int_value_wrapper(result, 'J_bl', "Number of vertices with id = od")
        return [measure_index, value1, value2, value3]


class MatchingIndex(Degree):
    """
    """
    _ui_name = "Matching Index: Connection/adjacency matrix"
    _ui_description = bct_description("matching_ind.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.matching_ind(connectivity.weights)
        result = {
            'Min': result[0],
            'Mout': result[1],
            'Mall': result[2]
        }
        measure_index1 = self.build_connectivity_measure(result, 'Min', connectivity,
                                                         "Matching index for incoming connections")
        measure_index2 = self.build_connectivity_measure(result, 'Mout', connectivity,
                                                         "Matching index for outgoing connections")
        measure_index3 = self.build_connectivity_measure(result, 'Mall', connectivity,
                                                         "Matching index for all connections")
        return [measure_index1, measure_index2, measure_index3]


class Strength(Degree):
    """
    """
    _ui_name = "Strength: Directed weighted connection matrix"
    _ui_description = bct_description("strengths_und.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = {'strength': bct.strengths_und(connectivity.weights)}
        measure_index = self.build_connectivity_measure(result, 'strength', connectivity, "Node strength")
        return [measure_index]


class StrengthISOS(Strength):
    """
    """
    _ui_name = "Instrength and Outstrength"
    _ui_description = bct_description("strengths_dir.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.strengths_dir(connectivity.weights)
        result = {
            'is': result[0],
            'os': result[1],
            'strength': result[2]
        }
        measure_index1 = self.build_connectivity_measure(result, 'is', connectivity, "Node instrength")
        measure_index2 = self.build_connectivity_measure(result, 'os', connectivity, "Node outstrength")
        measure_index3 = self.build_connectivity_measure(result, 'strength', connectivity,
                                                         "Node strength (instrength + outstrength)")
        return [measure_index1, measure_index2, measure_index3]


class StrengthWeights(Strength):
    """
    """
    _ui_name = "Strength and Weight"
    _ui_description = bct_description("strengths_und_sign.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.strengths_und_sign(connectivity.weights)
        result = {
            'Spos': result[0],
            'Sneg': result[1],
            'vpos': result[2],
            'vneg': result[3]
        }
        measure_index1 = self.build_connectivity_measure(result, 'Spos', connectivity,
                                                         "Nodal strength of positive weights")
        measure_index2 = self.build_connectivity_measure(result, 'Sneg', connectivity,
                                                         "Nodal strength of negative weights")
        value1 = self.build_float_value_wrapper(result, 'vpos', "Total positive weight")
        value2 = self.build_float_value_wrapper(result, 'vneg', "Total negative weight")
        return [measure_index1, measure_index2, value1, value2]


class DensityDirected(BaseBCT):
    """
    """
    _ui_group = BCT_GROUP_DENSITY

    _ui_name = "Density Directed: Directed (weighted/binary) connection matrix"
    _ui_description = bct_description("density_dir.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.density_dir(connectivity.weights)
        result = {
            'kden': result[0],
            'N': result[1],
            'K': result[2]
        }
        value1 = self.build_float_value_wrapper(result, 'kden', title="Density")
        value2 = self.build_int_value_wrapper(result, 'N', title="Number of vertices")
        value3 = self.build_int_value_wrapper(result, 'K', title="Number of edges")
        return [value1, value2, value3]


class DensityUndirected(DensityDirected):
    """
    """
    _ui_name = "Density Unirected: Undirected (weighted/binary) connection matrix"
    _ui_description = bct_description("density_und.m")

    def launch(self, view_model):
        connectivity = self.get_connectivity(view_model)
        result = bct.density_und(connectivity.weights)
        result = {
            'kden': result[0],
            'N': result[1],
            'K': result[2]
        }
        value1 = self.build_float_value_wrapper(result, 'kden', title="Density")
        value2 = self.build_int_value_wrapper(result, 'N', title="Number of vertices")
        value3 = self.build_int_value_wrapper(result, 'K', title="Number of edges")
        return [value1, value2, value3]
