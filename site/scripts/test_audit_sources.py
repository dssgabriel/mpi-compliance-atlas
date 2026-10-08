"""Negative-evidence and stub checks for the release source inventory."""
import io
import pathlib
import tarfile
import tempfile
import unittest

import audit_sources as audit


class SourceAuditTests(unittest.TestCase):
    def test_comments_and_strings_are_not_definitions(self):
        text = '/* int MPI_Fake(void) { return 0; } */\nconst char *s="MPI_Fake() {}";\nint MPI_Send(void) { return backend(); }'
        self.assertEqual([m[1] for m in audit.DEFINITION.finditer(audit.mask(text))],['MPI_Send'])

    def test_continued_string_keeps_function_braces(self):
        text = 'int MPI_Error_string(void) { const char *s="continued \\\n string"; return backend(s); }\n'
        code=audit.mask(text);definition=next(audit.DEFINITION.finditer(code))
        self.assertIn('return backend(s);',audit.body_at(code,definition.end()))

    def test_declaration_and_call_are_not_definitions(self):
        text = 'int MPI_Send(int n);\nvoid wrapper(void) { MPI_Send(0); }'
        self.assertFalse(list(audit.DEFINITION.finditer(audit.mask(text))))

    def test_argument_error_path_is_not_an_unconditional_stub(self):
        self.assertIsNone(audit.stub_reason('if (bad_arg) { abort(); } return backend();','MPI_Send'))
        self.assertIsNone(audit.stub_reason('if (unsupported_option) { not_implemented(); } return backend();','MPI_Send'))
        self.assertIn('not-implemented',audit.stub_reason('if (bad_arg) { return MPI_ERR_ARG; } not_implemented();','MPI_Send'))

    def test_mpi_abort_and_pcontrol_are_legitimate(self):
        self.assertIsNone(audit.stub_reason('abort();','MPI_Abort'))
        self.assertIsNone(audit.stub_reason('(void)level; return MPI_SUCCESS;','MPI_Pcontrol'))
        self.assertIsNone(audit.stub_reason('return MPI_SUCCESS;','MPI_NULL_DELETE_FN'))

    def test_terminal_stub_and_empty_candidate(self):
        self.assertIn('termination',audit.stub_reason('abort(); return 0;','MPI_Send'))
        self.assertIn('not-implemented',audit.stub_reason('NOT_IMPLEMENTED(); return 0;','MPI_Send'))
        self.assertIn('semantic review',audit.stub_reason('return MPI_SUCCESS;','MPI_Send'))
        self.assertIn('semantic review',audit.stub_reason('UNUSED(output); return MPI_SUCCESS;','MPI_T_event_get_source'))
        self.assertIn('NOT_SUPPORTED',audit.stub_reason('UNUSED(output); return MPI_T_ERR_NOT_SUPPORTED;','MPI_T_source_get_info'))

    def archive(self, directory, root, complete=True):
        path=pathlib.Path(directory)/'source.tar.gz'
        with tarfile.open(path,'w:gz') as tar:
            bodies={f'MPI_Sample{i}':'return backend();' for i in range(100 if complete else 2)}
            bodies.update(MPI_Send='return backend();', MPI_Abort='abort();', MPI_Pcontrol='return 0;',
                          MPI_Fatal='NOT_IMPLEMENTED();',MPI_Empty='return 0;')
            for name,body in bodies.items():
                text=f'int {name}(void) {{ {body} }}\n'.encode()
                item=tarfile.TarInfo(f'{root}/ompi/mpi/c/{name}.c');item.size=len(text)
                tar.addfile(item,io.BytesIO(text))
            for subpath in ['ompi/mpi/c/decl.h','tests/fake.c']:
                text=b'int MPI_Declared(void);\nint MPI_TestOnly(void) { return backend(); }\n' if subpath.startswith('tests') else b'int MPI_Declared(void);\n'
                item=tarfile.TarInfo(f'{root}/{subpath}');item.size=len(text);tar.addfile(item,io.BytesIO(text))
        return path

    def test_missing_stub_declared_and_test_only(self):
        with tempfile.TemporaryDirectory() as directory:
            release=audit.RELEASES['openmpi'];path=self.archive(directory,release['archive_root'])
            names={f'MPI_Sample{i}' for i in range(100)}|{'MPI_Send','MPI_Abort','MPI_Pcontrol','MPI_Fatal','MPI_Empty','MPI_Declared','MPI_Missing','MPI_TestOnly'}
            rows=audit.scan_archive(path,'openmpi',release,names)['rows']
            self.assertEqual(rows['MPI_Send']['status'],'supported')
            self.assertEqual(rows['MPI_Fatal']['status'],'unsupported')
            self.assertEqual(rows['MPI_Empty']['status'],'unknown')
            self.assertEqual(rows['MPI_Declared']['status'],'unknown')
            self.assertEqual(rows['MPI_Missing']['status'],'unsupported')
            self.assertEqual(rows['MPI_TestOnly']['status'],'unsupported')
            self.assertIn('/v5.0.10/',rows['MPI_Send']['source'])

    def test_wrong_version_and_incomplete_tree_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            release=audit.RELEASES['openmpi']
            with self.assertRaisesRegex(ValueError,'expected archive root'):
                audit.scan_archive(self.archive(directory,'openmpi-5.0.9'),'openmpi',release,{'MPI_Send'})
            with self.assertRaisesRegex(ValueError,'incomplete/unrecognized'):
                audit.scan_archive(self.archive(directory,release['archive_root'],complete=False),'openmpi',release,{'MPI_Send'})


if __name__=='__main__':unittest.main()
