from pathlib import Path
import tempfile
import unittest
from coverage_fixes import declared_plugin_in_parent_chain, preserve_project_language_flags


class CoverageFixesTests(unittest.TestCase):
    def test_inherited_plugin_is_detected_without_changing_pom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'project/pom.xml'
            child.parent.mkdir()
            data = ('<project xmlns="http://maven.apache.org/POM/4.0.0"><parent>'
                    '<groupId>com.example</groupId><artifactId>base</artifactId><version>1</version>'
                    '<relativePath/></parent></project>')
            child.write_text(data)
            parent = root / 'repo/com/example/base/1/base-1.pom'
            parent.parent.mkdir(parents=True)
            parent.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"><build>'
                              '<plugins><plugin><groupId>pl.project13.maven</groupId>'
                              '<artifactId>git-commit-id-plugin</artifactId></plugin></plugins>'
                              '</build></project>')
            self.assertTrue(declared_plugin_in_parent_chain(child, root / 'repo',
                'pl.project13.maven', 'git-commit-id-plugin'))
            self.assertEqual(data, child.read_text())

    def test_missing_parent_is_not_silently_treated_as_no_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'pom.xml'
            child.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"><parent>'
                '<groupId>x</groupId><artifactId>base</artifactId><version>1</version>'
                '<relativePath/></parent></project>')
            with self.assertRaises(FileNotFoundError):
                declared_plugin_in_parent_chain(child, root / 'repo', 'x', 'plugin')

    def test_language_fix_does_not_disable_or_exclude_tests(self):
        original = ['mvn', '-DskipTests', '-Dmaven.compiler.source=8',
                    '-Dmaven.compiler.target=8', '-pl', 'common,microbench', '-am', 'install']
        fixed = preserve_project_language_flags(original)
        self.assertNotIn('-Dmaven.compiler.source=8', fixed)
        self.assertNotIn('-Dmaven.compiler.target=8', fixed)
        self.assertEqual(['mvn', '-DskipTests', '-pl', 'common,microbench', '-am', 'install'], fixed)
        self.assertIn('-Dmaven.compiler.source=8', original)


if __name__ == '__main__':
    unittest.main()
