# Python Version: 3.x
import functools
import pathlib
import subprocess
from logging import getLogger
from typing import *

from onlinejudge_verify.config import get_config
from onlinejudge_verify.languages.models import Language, LanguageEnvironment
from onlinejudge_verify.languages.special_comments import list_special_comments, list_doxygen_annotations

logger = getLogger(__name__)


class RustLanguageEnvironment(LanguageEnvironment):
    RUSTFLAGS: List[str]

    def __init__(self, *, RUSTFLAGS: List[str]):
        self.RUSTFLAGS = RUSTFLAGS

    def compile(self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path):
        command = ["rustc", "-o",
                   f"{str(tempdir/'a.out')}"] + self.RUSTFLAGS+[str(path)]
        logger.info('$ %s', ' '.join(command))
        subprocess.check_call(command)

    def get_execute_command(self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path) -> List[str]:
        return [str(tempdir / "a.out")]


@functools.lru_cache(maxsize=None)
def _list_direct_dependencies(path: pathlib.Path, *, basedir: pathlib.Path) -> List[pathlib.Path]:
    dependencies = [path.resolve()]
    with open(path, 'rb') as fh:
        for line in fh.read().decode().splitlines():
            line = line.strip()
            if line.startswith('pub'):
                line = line[3:].strip()
            if line.startswith('mod'):
                line = line[3:].strip().strip(";").replace("::", "/")
            else:
                continue
            item_ = (path.parent/pathlib.Path(line+".rs"))
            mod_item_ = (path.parent/pathlib.Path(line+"/mod.rs"))
            print(item_.absolute())
            if item_.exists():
                dependencies.append(item_.absolute())
            elif mod_item_.exists():
                dependencies.extend(_list_direct_dependencies(
                    mod_item_.absolute(), basedir=basedir))
    return list(set(dependencies))


class RustLanguage(Language):
    config: Dict[str, Any]

    def __init__(self, *, config: Optional[Dict[str, Any]] = None):
        if config is None:
            self.config = get_config().get('languages', {}).get('rust', {})
        else:
            self.config = config

    def list_dependencies(self, path: pathlib.Path, *, basedir: pathlib.Path) -> List[pathlib.Path]:
        dependencies = []
        visited: Set[pathlib.Path] = set()
        stk = [path.resolve()]
        while stk:
            path = stk.pop()
            if path in visited:
                continue
            visited.add(path)
            for child in _list_direct_dependencies(path, basedir=basedir):
                dependencies.append(child)
                stk.append(child)
            return list(set(dependencies))

    def bundle(self, path: pathlib.Path, *, basedir: pathlib.Path) -> bytes:
        raise NotImplementedError

    def is_verification_file(self, path: pathlib.Path, *, basedir: pathlib.Path) -> bool:
        return path.name.endswith("_test.rs")

    def list_environments(self, path: pathlib.Path, *, basedir: pathlib.Path) -> List[RustLanguageEnvironment]:
        default_RUSTFLAGS = []
        envs = []
        if 'environments' not in self.config:
            envs.append(RustLanguageEnvironment(RUSTFLAGS=default_RUSTFLAGS))
        else:
            for env in self.config['environments']:
                RUSTFLAGS: List[str] = env.get('RUSTFLAGS', default_RUSTFLAGS)
                if not isinstance(RUSTFLAGS, list):
                    raise RuntimeError('RUSTFLAGS must be a list')
                envs.append(RustLanguageEnvironment(RUSTFLAGS=RUSTFLAGS))
        return envs

    def list_attributes(self, path: pathlib.Path, *, basedir: pathlib.Path) -> Dict[str, str]:
        return list_special_comments(path.resolve()) or list_doxygen_annotations(path.resolve())
