import openmc
# my_mats = odw.Materials(....)

# newtally = odw.CellTally(reaction='TBR', filter=openmc.MaterialFilter(my_-mats.materials[0]))
# newtally = odw.CellTally(reaction='TBR', material_filter=["tungsten"])
# newtally = odw.CellTally(reaction='TBR', target=1)
# newtally = odw.CellTally(reaction='TBR', target="tungsten")
# newtally = odw.CellTally(score='TBR', target="tungsten", materials=my_mats)

# my_tallies = odw.CellTalliesOnVolumes(reaction='TBR', target, [1])


class CellTally(openmc.Tally):
    """Usage:
    my_mats = odw.Materials(....)
    my_tally = odw.CellTally(odw_score='TBR', target="tungsten", materials=my_mats)
    my_tally2 = odw.CellTally(odw_score='TBR', target=2)
    my_tally3 = odw.CellTally(odw_score='TBR')

    Args:
        odw_score ([type]): [description]
        target ([type]): [description]
        materials ([type]): [description]
    """
    def __init__(self, odw_score, target=None, materials=None, **kwargs):
        self.odw_score = odw_score
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

        if self.odw_score == "TBR":
            self.scores = "(n,Xt)"  # where X is a wild card
        elif self.odw_score in flux_scores:
            self.scores = "flux"
        else:
            self.scores = self.odw_score

    def set_name(self):
        if self.target is not None:
            self.name = str(self.target) + "_" + self.odw_score
        else:
            self.name = self.odw_score

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
        if self.odw_score == "neutron_fast_flux":
            energy_bins = [1e6, 1000e6]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [neutron_particle_filter, energy_filter]
        elif self.odw_score == "photon_fast_flux":
            energy_bins = [1e6, 1000e6]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [photon_particle_filter, energy_filter]
        elif self.odw_score == "neutron_spectra":
            energy_bins = openmc.mgxs.GROUP_STRUCTURES["CCFE-709"]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [neutron_particle_filter, energy_filter]
        elif self.odw_score == "photon_spectra":
            energy_bins = openmc.mgxs.GROUP_STRUCTURES["CCFE-709"]
            energy_filter = openmc.EnergyFilter(energy_bins)
            additional_filters = [photon_particle_filter, energy_filter]
        elif self.odw_score == "neutron_effective_dose":
            energy_function_filter_n = openmc.EnergyFunctionFilter(
                energy_bins_n, dose_coeffs_n)
            additional_filters = [
                neutron_particle_filter, energy_function_filter_n]
        elif self.odw_score == "photon_effective_dose":
            energy_function_filter_n = openmc.EnergyFunctionFilter(
                energy_bins_n, dose_coeffs_n)
            additional_filters = [
                photon_particle_filter, energy_function_filter_n]

        self.filters = [tally_filter] + additional_filters


class TetMeshTally(openmc.Tally):
    """Usage:
    my_tally = odw.TetMeshTally(odw_score='TBR', filename="file.h5m")
    my_tally2 = odw.TetMeshTally(odw_score='TBR', filename="file.exo")

    Args:
        odw_score ([type]): [description]
        filename (str): [description]
    """
    def __init__(self, odw_score, filename, **kwargs):
        self.filename = filename
        super().__init__(**kwargs)

        self.create_unstructured_mesh()
        self.filters = [openmc.MeshFilter(self.umesh)]
        self.scores = [odw_score]  # @shimwell should this be done as in CellTally.set_score?
        self.name = odw_score + "_on_3D_u_mesh"

    def create_unstructured_mesh(self):
        if self.filename.endswith(".exo"):
            # requires a exo file export from cubit
            self.umesh = openmc.UnstructuredMesh(
                self.filename, library="libmesh"
            )
        elif self.filename.endswith(".h5m"):
            # requires a .cub file export from cubit and mbconvert to h5m
            # format
            self.umesh = openmc.UnstructuredMesh(
                self.filename, library="moab")
        else:
            msg = ("only h5m or exo files are accepted as valid "
                   "filename values")
            raise ValueError(msg)


class CellTallies:
    """
    Collection of odw.CellTally objects stored in self.tallies

    Usage:
    my_mats = odw.Materials(....)
    my_tallies = odw.CellTallies(odw_scores=['TBR', "flux"], target=["tungsten", 2], materials=my_mats)
    my_tallies = odw.CellTallies(odw_scores=['TBR', "flux"], target=[2])

    Args:
        odw_scores ([type]): [description]
        targets (list, optional): [description]. Defaults to [None].
        materials ([type], optional): [description]. Defaults to None.
    """
    def __init__(self, odw_scores, targets=[None], materials=None):
        self.tallies = []
        self.odw_scores = odw_scores
        self.targets = targets
        self.materials = materials
        for score in self.odw_scores:
            for target in self.targets:
                self.tallies.append(
                    CellTally(
                        odw_score=score,
                        target=target,
                        materials=materials)
                        )


class TetMeshTallies:
    """Collection of TetMeshTally objects stored in self.tallies
    my_tally = odw.TetMeshTally(odw_scores=['TBR'], filename=["file1.h5m", "file2.exo"])
    Args:
        odw_scores (list): [description]
        filenames (list): [description]
    """
    def __init__(self, odw_scores, filenames):
        self.tallies = []
        self.odw_scores = odw_scores
        for score in self.odw_scores:
            for filename in filenames:
                self.tallies.append(
                    TetMeshTally(odw_score=score, filename=filename))

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
