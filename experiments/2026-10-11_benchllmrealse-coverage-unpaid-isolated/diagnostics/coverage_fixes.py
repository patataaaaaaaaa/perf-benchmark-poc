"""Candidate preparation helpers; deliberately NOT imported by the active runner."""
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}


def declared_plugin_in_parent_chain(pom, repository, group, artifact):
    """Check explicit parent coordinates offline, including pluginManagement.

    This is not a complete Maven effective-model implementation. Unsupported
    property interpolation or missing parents fail closed, not silently False.
    """
    pom, repository = Path(pom), Path(repository)
    visited = set()
    while True:
        if pom.resolve() in visited:
            raise ValueError('Cyclic parent POM chain')
        visited.add(pom.resolve())
        element = ET.parse(pom).getroot()
        for plugin in element.findall('.//m:plugin', NS):
            gid = plugin.findtext('m:groupId', 'org.apache.maven.plugins', NS)
            aid = plugin.findtext('m:artifactId', '', NS)
            if (gid, aid) == (group, artifact):
                return True
        parent = element.find('m:parent', NS)
        if parent is None:
            return False
        coords = [parent.findtext('m:' + name, '', NS)
                  for name in ('groupId', 'artifactId', 'version')]
        if not all(coords) or any('${' in value for value in coords):
            raise ValueError('Parent coordinates require Maven model resolution')
        relative = parent.findtext('m:relativePath', '../pom.xml', NS)
        local = (pom.parent / relative).resolve() if relative else None
        if local is not None and local.is_file():
            local_root = ET.parse(local).getroot()
            own = [local_root.findtext('m:' + name, '', NS)
                   for name in ('groupId', 'artifactId', 'version')]
            if own == coords:
                pom = local
                continue
        gid, aid, version = coords
        pom = repository / gid.replace('.', '/') / aid / version / (aid + '-' + version + '.pom')
        if not pom.is_file():
            raise FileNotFoundError('Required offline parent POM is missing: ' + str(pom))


def preserve_project_language_flags(flags):
    """Do not force legacy Netty test sources into Java 8 type inference.

    Leave the original POM/profiles in control; do not delete or rewrite tests.
    The caller must still use the historical compatible JDK and run real tests.
    """
    return [flag for flag in flags
            if not flag.startswith(('-Dmaven.compiler.source=', '-Dmaven.compiler.target='))]
