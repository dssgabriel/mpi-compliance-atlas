"""Check semantic distinctions and exact standard ownership."""
import json
import pathlib
import unittest

from standard_taxonomy import classify, CHAPTERS, GROUPING


class StandardTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = pathlib.Path(__file__).resolve().parents[1] / 'dist/apis.json'
        cls.rows = {r['name']: r for r in json.loads(path.read_text())['rows']}

    def classified(self, name):
        return classify(name, self.rows[name]['section'])

    def test_every_catalog_entry_has_evidenced_chapter(self):
        for name, row in self.rows.items():
            result = classify(name, row['section'])
            self.assertIn(result['kind'], CHAPTERS, name)
            self.assertTrue(result['family'], name)
            self.assertTrue(result['taxonomy_source'], name)

    def test_exact_vault_ownership_overrides_name_prefixes(self):
        expectations = {
            'MPI_Type_get_value_index': 'colls',
            'MPI_Op_create': 'colls',
            'MPI_Neighbor_allgather': 'topology',
            'MPI_Session_attach_buffer': 'p2p',
            'MPI_Comm_create_errhandler': 'environment',
            'MPI_Grequest_start': 'external',
            'MPI_Type_create_keyval': 'communicator',
            'MPI_Comm_spawn': 'process',
        }
        for name, kind in expectations.items():
            self.assertEqual(self.classified(name)['kind'], kind, name)

    def test_persistent_form_is_not_procedure_blocking(self):
        send = self.classified('MPI_Send_init')
        bcast = self.classified('MPI_Bcast_init')
        self.assertEqual(send['operation_form'], 'persistent')
        self.assertEqual(bcast['operation_form'], 'persistent')
        self.assertEqual(send['procedure_blocking'], 'nonblocking')
        self.assertEqual(bcast['procedure_blocking'], 'blocking')

    def test_completion_and_queries_do_not_inherit_operation_form(self):
        for name in ('MPI_Wait', 'MPI_Test', 'MPI_Iprobe', 'MPI_Op_create'):
            self.assertIsNone(self.classified(name)['operation_form'], name)

    def test_rma_does_not_claim_blocking_completion(self):
        put = self.classified('MPI_Put')
        rput = self.classified('MPI_Rput')
        self.assertIsNone(put['operation_form'])
        self.assertEqual(put['rma_completion'], 'RMA synchronization')
        self.assertEqual(rput['rma_completion'], 'request-based local completion')

    def test_io_positioning_and_coordination_are_orthogonal(self):
        row = self.classified('MPI_File_iread_at_all')
        self.assertEqual(row['operation_form'], 'nonblocking')
        self.assertEqual(row['io_positioning'], 'explicit offset')
        self.assertEqual(row['io_coordination'], 'collective')
        ordered = self.classified('MPI_File_read_ordered')
        self.assertEqual(ordered['io_positioning'], 'shared file pointer')
        self.assertEqual(ordered['io_coordination'], 'collective')

    def test_large_count_bindings_share_exact_heading_path(self):
        for name in ('MPI_Send', 'MPI_Bcast', 'MPI_File_read_at_all'):
            self.assertEqual(GROUPING['rows'][name]['section_path'],
                             GROUPING['rows'][name + '_c']['section_path'])

    def test_legacy_lifecycle_does_not_create_fake_functional_chapter(self):
        self.assertEqual(self.classified('MPI_Type_struct')['kind'], 'datatypes')
        self.assertEqual(self.classified('MPI_Info_get')['kind'], 'info')
        self.assertEqual(self.classified('MPI_Get_elements_x')['kind'], 'datatypes')

    def test_fallback_evidence_is_explicit_and_exact_evidence_is_pinned(self):
        fallback = self.classified('MPI_Comm_toint')
        self.assertEqual(fallback['classification_method'], 'binding-summary fallback')
        self.assertIn('functional fallback', fallback['classification_basis'])
        exact = self.classified('MPI_Send')
        self.assertEqual(exact['classification_method'], 'exact vault heading path')
        self.assertIn('/blob/' + GROUPING['revision'] + '/', exact['taxonomy_source'])
        self.assertNotIn('/blob/main/', exact['taxonomy_source'])


if __name__ == '__main__':
    unittest.main()
