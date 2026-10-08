"""Check vault parsing and independent catalogue coverage decisions."""
import json
import pathlib
import tempfile
import unittest

from audit_standard import read_bindings

ROOT = pathlib.Path(__file__).resolve().parents[1]


class StandardAuditTests(unittest.TestCase):
    def test_callback_typedef_is_not_a_callable_api(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'signatures.json'
            path.write_text(json.dumps({'functions': [
                {'lis_name': 'MPI_SEND', 'chapter': 'pt2pt', 'c_bindings': [
                    'int MPI_Send(const void *buf, int count)',
                    'int MPI_Send_c(const void *buf, MPI_Count count)']},
                {'lis_name': 'MPI_USER_FUNCTION', 'chapter': 'coll', 'c_bindings': [
                    'typedef void MPI_User_function(void *invec)']},
                {'lis_name': 'MPI_CONVERSION_FN_NULL_C', 'chapter': 'io', 'c_bindings': [
                    'int MPI_CONVERSION_FN_NULL_C(void *buf, MPI_Count count)']},
            ]}))
            bindings, typedefs, _ = read_bindings(path)
            self.assertEqual(set(bindings), {'MPI_Send', 'MPI_Send_c', 'MPI_CONVERSION_FN_NULL_C'})
            self.assertEqual(set(typedefs), {'MPI_User_function'})

    def test_generated_catalogue_matches_verified_vault_inventory(self):
        report = json.loads((ROOT / 'data/standard-vault-audit.json').read_text())
        catalogue = json.loads((ROOT / 'dist/apis.json').read_text())
        rows = {row['name']: row for row in catalogue['rows']}
        standard_names = {name for name, row in rows.items() if row['lifecycle'] != 'removed'}
        self.assertEqual(standard_names, set(report['bindings']))
        self.assertEqual(len(standard_names), 704)
        self.assertEqual(len(rows), 714)
        for name, reference in report['bindings'].items():
            self.assertEqual(rows[name]['c_prototype'], reference['prototype'])
        self.assertEqual(rows['MPI_Status_set_elements_c']['introduced'], '4.1')
        self.assertIn('errata', rows['MPI_Status_set_elements_c']['introduction_note'])
        self.assertEqual(rows['MPI_CONVERSION_FN_NULL']['introduced'], '3.0')
        self.assertEqual(rows['MPI_CONVERSION_FN_NULL_C']['entry_type'], 'callback sentinel')


if __name__ == '__main__':
    unittest.main()
