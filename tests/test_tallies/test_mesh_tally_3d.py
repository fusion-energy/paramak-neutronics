import tarfile
import unittest
import urllib.request
from pathlib import Path
import zipfile
import openmc
import openmc_dagmc_wrapper as odw


class TestMeshTally3D(unittest.TestCase):
    """Tests the MeshTally3D class functionality"""

    def setUp(self):

        if not Path("tests/output_files_produced.zip").is_file():
            url = "https://github.com/fusion-energy/fusion_neutronics_workflow/releases/download/0.0.8/output_files_produced.zip"
            urllib.request.urlretrieve(url, "tests/output_files_produced.zip")

        with zipfile.ZipFile("tests/output_files_produced.zip", "r") as zip_ref:
            zip_ref.extractall("tests")

        self.h5m_filename_smaller = (
            "tests/example_01_single_volume_cell_tally/dagmc.h5m"
        )
        self.h5m_filename_bigger = "tests/example_02_multi_volume_cell_tally/dagmc.h5m"

    def test_incorrect_mesh_tally_3d(self):
        """Set a mesh_tally_3d that is not accepted which should raise an
        error"""

        def incorrect_mesh_tally_3d():
            odw.MeshTally3D("coucou", bounding_box=[(10, 10, 10), (-10, -10, -10)])

        self.assertRaises(ValueError, incorrect_mesh_tally_3d)

    def test_incorrect_mesh_tally_3d_type(self):
        """Set a mesh_tally_3d that is the wrong type which should raise an
        error"""

        def incorrect_mesh_tally_3d_type():
            odw.MeshTally3D(1, bounding_box=[(10, 10, 10), (-10, -10, -10)])

        self.assertRaises(TypeError, incorrect_mesh_tally_3d_type)

    def test_meshfilter_from_h5m_file(self):
        # build
        geometry = odw.Geometry(self.h5m_filename_smaller)
        expected_mesh = openmc.RegularMesh(mesh_id=99, name="3d_mesh_expected")
        bbox = geometry.corners()
        expected_mesh.lower_left = bbox[0]
        expected_mesh.upper_right = bbox[1]
        expected_mesh.dimension = (100, 100, 100)

        # run
        my_tally = odw.MeshTally3D(
            "heating",
            bounding_box=geometry.corners(),
        )
        produced_filter = my_tally.filters[-1]
        produced_mesh = produced_filter.mesh
        # test
        assert produced_mesh.lower_left == expected_mesh.lower_left
        assert produced_mesh.upper_right == expected_mesh.upper_right
        for produced_index, expected_index in zip(
            produced_mesh.indices, expected_mesh.indices
        ):
            assert produced_index == expected_index

    def test_meshfilter_from_custom_mesh(self):
        # build
        bbox = [(0, 0, 0), (1, 2, 3)]
        expected_mesh = openmc.RegularMesh(mesh_id=99, name="3d_mesh_expected")
        expected_mesh.lower_left = bbox[0]
        expected_mesh.upper_right = bbox[1]
        expected_mesh.dimension = (100, 100, 100)

        # run
        my_tally = odw.MeshTally3D("heating", bounding_box=bbox)
        produced_filter = my_tally.filters[-1]
        produced_mesh = produced_filter.mesh
        # test
        assert produced_mesh.lower_left == expected_mesh.lower_left
        assert produced_mesh.upper_right == expected_mesh.upper_right
        for produced_index, expected_index in zip(
            produced_mesh.indices, expected_mesh.indices
        ):
            assert produced_index == expected_index


if __name__ == "__main__":
    unittest.main()
