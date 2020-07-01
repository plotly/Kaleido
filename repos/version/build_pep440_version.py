import subprocess
import os


def git_pep440_version(path):
    def git_command(args):
        prefix = ['git', '-C', path]
        return str(subprocess.check_output(prefix + args).decode().strip())
    version_full = git_command(['describe', '--tags', '--dirty=.dirty'])
    version_tag = git_command(['describe', '--tags', '--abbrev=0'])

    # Strip leaving v (e.g. "v0.0.1" -> "0.0.1")
    if version_tag[0] == "v":
        version_tag = version_tag[1:]
        version_tail = version_full[len(version_tag) + 1:]
    else:
        version_tail = version_full[len(version_tag):]

    return version_tag + version_tail.replace('-', '.dev', 1).replace('-', '+', 1)


if __name__ == "__main__":
    repo_path = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))))
    version_file_path = os.path.join(repo_path, "repos", "kaleido", 'version')
    version = git_pep440_version(repo_path)
    with open(version_file_path, 'w') as f:
        f.write(version)
    print("Wrote {version} to {version_file_path}".format(
        version=version,
        version_file_path=version_file_path,
    ))
