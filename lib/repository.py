import os
import configparser


class GitRepository(object):
    """Represents a Git repository"""

    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False):
        """
        Initializes a GitRepository object.

        Args:
            path (str): The path to the repository.
            force (bool): If True, bypass checks for existing Git repository.
        """
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        # Check if the specified directory is a Git repository
        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("Not a Git repository %s" % path)

        # Initialize configuration parser
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        # Check if the configuration file exists
        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        # Check the repository format version
        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(
                    "Unsupported repositoryformatversion %s" % vers)

# region Utility Methods


def repo_path(repo, *path):
    """
    Computes a path under the repository's .git directory.

    Args:
        repo (GitRepository): The GitRepository object.
        *path (str): Components of the path to compute.

    Returns:
        str: The computed path.
    """
    return os.path.join(repo.gitdir, *path)


def repo_file(repo, *path, mkdir=False):
    """
    Computes a file path under the repository's .git directory and creates any necessary directories.

    Args:
        repo (GitRepository): The GitRepository object.
        *path (str): Components of the file path to compute.
        mkdir (bool): If True, create directories up to the last component.

    Returns:
        str: The file path.
    """
    # Create directories if necessary
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo, *path, mkdir=False):
    """
    Computes a directory path under the repository's .git directory and optionally creates it.

    Args:
        repo (GitRepository): The GitRepository object.
        *path (str): Components of the directory path to compute.
        mkdir (bool): If True, create the directory if it does not exist.

    Returns:
        str: The directory path, or None if the directory was not created.
    """
    path = repo_path(repo, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception("Not a directory %s" % path)

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repo_create(path):
    """
    Creates a new Git repository at the specified path.

    Args:
        path (str): The path where the new repository will be created.

    Returns:
        GitRepository: The newly created GitRepository object.
    """
    repo = GitRepository(path, True)

    # Check if the path is a valid directory and is empty
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception("%s is not a directory!" % path)
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception("%s is not empty!" % path)
    else:
        os.makedirs(repo.worktree)

    # Create necessary directories and files
    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # Create .git/description file
    with open(repo_file(repo, "description"), "w") as f:
        f.write(
            "Unnamed repository; edit this file 'description' to name the repository.\n")

    # Create .git/HEAD file
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    # Create .git/config file with default configuration
    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo


def repo_default_config():
    """
    Creates the default configuration for a new Git repository.

    Returns:
        configparser.ConfigParser: The default configuration.
    """
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret


def repo_find(path=".", required=True):
    """
    Finds the root of a Git repository by searching upwards from the specified path.

    Args:
        path (str): The starting path for the search.
        required (bool): If True, raise an exception if no Git repository is found.

    Returns:
        GitRepository: The GitRepository object if found.

    Raises:
        Exception: If no Git repository is found and required is True.
    """
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    # Recurse up to parent directory
    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        # Reached the root directory
        if required:
            raise Exception("No git directory.")
        else:
            return None

    # Recursive case
    return repo_find(parent, required)

# endregion
