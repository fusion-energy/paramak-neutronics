
from typing import Union

import openmc
from openmc_dagmc_wrapper import Materials

# my_mats = odw.Materials(....)

# newtally = odw.CellTally(reaction='TBR', filter=openmc.MaterialFilter(my_-mats.materials[0]))
# newtally = odw.CellTally(reaction='TBR', material_filter=["tungsten"])
# newtally = odw.CellTally(reaction='TBR', target=1)
# newtally = odw.CellTally(reaction='TBR', target="tungsten")
# newtally = odw.CellTally(score='TBR', target="tungsten", materials=my_mats)

# my_tallies = odw.CellTalliesOnVolumes(reaction='TBR', target, [1])

    #  Usage:
    # my_mats = odw.Materials(....)
    # my_tally = odw.CellTally(score='TBR', target="tungsten", materials=my_mats)
    # my_tally2 = odw.CellTally(score='TBR', target=2)
    # my_tally3 = odw.CellTally(score='TBR')

class CellTally(openmc.Tally):
    """Extends the openmc.Tally object to allow a range of standard tally_types.
    Facilitates standardized combinations of tally openmc.Tally.scores and 
    openmc.Tally.filters to allow convenient application of tallies to specified
    materials or volumes.

    Args:
        tally_type: specify the standard tally from a the folloing options
             neutron_flux, photon_flux, neutron_fast_flux, photon_fast_flux,
             neutron_spectra, photon_spectra, neutron_effective_dose,
             photon_effective_dose, TBR. Also allows for standard openmc.scores
             to be specified from the available scores.
             https://docs.openmc.org/en/latest/usersguide/tallies.html#scores
        target: the volume id or the material tag to apply the tally to.
        materials: the openmc_dagmc_wrapper.Materials used in the openmc
            simulation. Only required if applying tallies to materials.
    """
    def __init__(
        self,
        tally_type: str,
        target: Union[int, str]=None,
        materials: Materials = None,
        **kwargs
    ):

        self.tally_type = tally_type
        self.targer = target
        self.materials = materials
        super().__init__(**kwargs)
        self.set_score()
        self.set_name()
        self.set_filter()

    def set_score(self):
        flux_scores = [
            "neutron_fast_flux", "photon_fast_flux",
            "neutron_spectra", "photon_spectra",
            "neutron_effective_dose", "photon_effective_dose"
        ]

        if self.tally_type == "TBR":
            self.scores = "(n,Xt)"  # where X is a wild card
        elif self.tally_type in flux_scores:
            self.scores = "flux"
        else:
            self.scores = self.tally_type

    def set_name(self):
        if self.target is not None:
            self.name = str(self.target) + "_" + self.tally_type
        else:
            self.name = self.tally_type

    def set_filter(self):
        energy_bins_n, dose_coeffs_n = openmc.data.dose_coefficients(
            particle="neutron",
            geometry="ISO",
        )
        energy_bins_p, dose_coeffs_p = openmc.data.dose_coefficients(
            particle="photon",
            geometry="ISO",
        )
        photon_particle_filter = openmc.ParticleFilter(["photon"])
        neutron_particle_filter = openmc.ParticleFilter(["neutron"])
        if type(self.target) is str:  # material filter
            for mat in self.materials.materials:
                if mat.name == self.target:
                    tally_filter = openmc.MaterialFilter(mat)
        elif type(self.target) is int:  # volume filter
            tally_filter = openmc.CellFilter(self.target)

        additional_filters = []
        if self.tally_type == "neutron_fast_flux":
            energy_bins = [1e6, 1000e6]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [neutron_particle_filter, energy_filter]
        elif self.tally_type == "photon_fast_flux":
            energy_bins = [1e6, 1000e6]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [photon_particle_filter, energy_filter]
        elif self.tally_type == "neutron_spectra":
            energy_bins = openmc.mgxs.GROUP_STRUCTURES["CCFE-709"]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [neutron_particle_filter, energy_filter]
        elif self.tally_type == "photon_spectra":
            energy_bins = openmc.mgxs.GROUP_STRUCTURES["CCFE-709"]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [photon_particle_filter, energy_filter]
        elif self.tally_type == "neutron_effective_dose":
            energy_function_filter_n = openmc.EnergyFunctionFilter(
                energy_bins_n, dose_coeffs_n)
            additional_filters = [
                neutron_particle_filter, energy_function_filter_n]
        elif self.tally_type == "photon_effective_dose":
            energy_function_filter_n = openmc.EnergyFunctionFilter(
                energy_bins_n, dose_coeffs_n)
            additional_filters = [
                photon_particle_filter, energy_function_filter_n]

        self.filters = [tally_filter] + additional_filters


class CellTallies:
    def __init__(self, tally_types, targets=[None], materials=None):
        self.tallies = []
        self.tally_types = tally_types
        self.targets = targets
        self.materials = materials
        for score in self.tally_types:
            for target in self.targets:
                self.tallies.append(CellTally(tally_type=score, target=target, materials=materials))


# # in neutronicsModel
# energy_bins_n, dose_coeffs_n = openmc.data.dose_coefficients(
#     particle="neutron",
#     geometry="ISO",
# )
# energy_bins_p, dose_coeffs_p = openmc.data.dose_coefficients(
#     particle="photon",
#     geometry="ISO",
# )
# photon_particle_filter = openmc.ParticleFilter(["photon"])
# neutron_particle_filter = openmc.ParticleFilter(["neutron"])

# for standard_tally in self.cell_tallies:
#     if standard_tally == "TBR":
#         score = "(n,Xt)"  # where X is a wild card
#         suffix = "TBR"
#         tally = openmc.Tally(name="TBR")
#         tally.scores = [score]
#         self.tallies.append(tally)
#         self._add_tally_for_every_material(suffix, score)

#     elif standard_tally == "fast_flux":

#         energy_bins = [1e6, 1000e6]
#         energy_filter = openmc.EnergyFilter(energy_bins)

#         self._add_tally_for_every_material(
#             "neutron_fast_flux",
#             "flux",
#             [neutron_particle_filter, energy_filter],
#         )
#         if self.photon_transport is True:
#             self._add_tally_for_every_material(
#                 "photon_fast_flux",
#                 "flux",
#                 [photon_particle_filter, energy_filter],
#             )

#     elif standard_tally == "spectra":

#         energy_bins = openmc.mgxs.GROUP_STRUCTURES["CCFE-709"]
#         energy_filter = openmc.EnergyFilter(energy_bins)

#         self._add_tally_for_every_material(
#             "neutron_spectra",
#             "flux",
#             [neutron_particle_filter, energy_filter],
#         )
#         if self.photon_transport is True:
#             self._add_tally_for_every_material(
#                 "photon_spectra",
#                 "flux",
#                 [photon_particle_filter, energy_filter],
#             )
#     elif standard_tally == "effective_dose":

#         energy_function_filter_n = openmc.EnergyFunctionFilter(
#             energy_bins_n, dose_coeffs_n
#         )

#         self._add_tally_for_every_material(
#             "neutron_effective_dose",
#             "flux",
#             [energy_function_filter_n, neutron_particle_filter],
#         )

#         if self.photon_transport:

#             energy_function_filter_p = openmc.EnergyFunctionFilter(
#                 energy_bins_p, dose_coeffs_p
#             )

#             self._add_tally_for_every_material(
#                 "photon_effective_dose",
#                 "flux",
#                 [energy_function_filter_p, photon_particle_filter],
#             )

#     else:
#         score = standard_tally
#         suffix = standard_tally
#         self._add_tally_for_every_material(suffix, score)

# def _add_tally_for_every_material(
#     self, suffix: str, score: str, additional_filters: List = None
# ) -> None:
#     """Adds a tally to self.tallies for every material.

#     Arguments:
#         suffix: the string to append to the end of the tally name to help
#             identify the tally later.
#         score: the openmc.Tally().scores value that contribute to the tally
#         additional_filters: A list of  filters to ad
#     """
#     if additional_filters is None:
#         additional_filters = []
#     for key, value in self.openmc_materials.items():
#         if key != "DT_plasma":
#             material_filter = openmc.MaterialFilter(value)
#             tally = openmc.Tally(name=key + "_" + suffix)
#             tally.filters = [material_filter] + additional_filters
#             tally.scores = [score]
#             self.tallies.append(tally)
