import re

import pytest

from galaxy_importer.schema import LegacyGalaxyInfo, LegacyMetadata, LegacyImportResult


@pytest.fixture
def galaxy_info():
    info = {
        "role_name": "my_role",
        "author": "shakespeare",
        "description": "incredible role",
        "company": "Red Hat",
        "issue_tracker_url": "https://www.github.com",
        "license": "MIT",
        "min_ansible_version": "2.4",
        "min_ansible_container_version": "2.0",
        "platforms": [
            {"name": "Fedora", "versions": "all"},
            {"name": "Debian", "versions": "['7.0']"},
        ],
        "galaxy_tags": ["docker", "ansible", "container"],
    }
    return info


def test_values(galaxy_info):
    info = LegacyGalaxyInfo(**galaxy_info)

    assert info.role_name == "my_role"
    assert info.author == "shakespeare"
    assert info.description == "incredible role"
    assert info.company == "Red Hat"
    assert info.issue_tracker_url == "https://www.github.com"
    assert info.license == "MIT"
    assert info.min_ansible_version == "2.4"
    assert info.min_ansible_container_version == "2.0"
    assert info.github_branch is None
    assert info.platforms == [
        {"name": "Fedora", "versions": "all"},
        {"name": "Debian", "versions": "['7.0']"},
    ]
    assert info.galaxy_tags == ["docker", "ansible", "container"]


def test_valid_str(galaxy_info):
    galaxy_info["role_name"] = []
    with pytest.raises(ValueError, match="must be a string"):
        LegacyGalaxyInfo(**galaxy_info)


def test_valid_list_dict(galaxy_info):
    galaxy_info["platforms"] = "string"
    with pytest.raises(ValueError, match=re.compile("must be a list$")):
        LegacyGalaxyInfo(**galaxy_info)

    galaxy_info["platforms"] = ["string", "other"]
    with pytest.raises(ValueError, match="must be a list of dictionaries"):
        LegacyGalaxyInfo(**galaxy_info)


def test_valid_list_str(galaxy_info):
    galaxy_info["galaxy_tags"] = "string"
    with pytest.raises(ValueError, match=re.compile("must be a list$")):
        LegacyGalaxyInfo(**galaxy_info)

    galaxy_info["galaxy_tags"] = [dict()]
    with pytest.raises(ValueError, match="must be a list of strings"):
        LegacyGalaxyInfo(**galaxy_info)


@pytest.mark.parametrize(
    "valid_name",
    [
        "this",
        "that",
        "walker_turzai",
        "foo_bar_baz",
        "name123_four",
        "r1",
        "crush_",
    ],
)
def test_valid_role_name(galaxy_info, valid_name):
    galaxy_info["role_name"] = valid_name
    info = LegacyGalaxyInfo(**galaxy_info)
    assert info.role_name == valid_name


@pytest.mark.parametrize(
    "invalid_name",
    [
        "_this",
        "walker-turzai",
        "foo_bar-baz",
        "3w6",
        "$@#",
        "this.role",
        "docker!",
        "big space",
        "whyUpper",
    ],
)
def test_invalid_role_name(galaxy_info, invalid_name):
    galaxy_info["role_name"] = invalid_name
    with pytest.raises(ValueError, match="role name is invalid"):
        LegacyGalaxyInfo(**galaxy_info)


def test_max_author(galaxy_info):
    galaxy_info["author"] = galaxy_info["author"] * 100
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)


def test_max_url(galaxy_info):
    galaxy_info["issue_tracker_url"] = galaxy_info["issue_tracker_url"] + ("/a" * 1001)
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)


def test_max_license(galaxy_info):
    galaxy_info["license"] = galaxy_info["license"] * 30
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)


def test_max_version(galaxy_info):
    galaxy_info["min_ansible_version"] = galaxy_info["min_ansible_version"] * 50
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)

    galaxy_info["min_ansible_version"] = "2.1"
    galaxy_info["min_ansible_container_version"] = galaxy_info["min_ansible_container_version"] * 50
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)


def test_max_tag(galaxy_info):
    galaxy_info["galaxy_tags"][0] = "rhel" * 100
    with pytest.raises(ValueError, match="must not exceed"):
        LegacyGalaxyInfo(**galaxy_info)


@pytest.mark.parametrize(
    "valid_dependency",
    [
        [],
        ["geerlingguy.php"],
        ["eamontracey.hello_role"],
        ["geerlingguy.php", "eamontracey.hello_role"],
    ],
)
def test_valid_dependencies(galaxy_info, valid_dependency):
    metadata = LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), valid_dependency)
    assert metadata.dependencies == valid_dependency


def test_invalid_dependency_type(galaxy_info):
    dependencies = [dict()]

    with pytest.raises(ValueError, match="must be a list of strings"):
        LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), dependencies)


def test_invalid_dependency_separation(galaxy_info):
    dependencies = ["foo.bar.baz"]

    with pytest.raises(ValueError, match="namespace and name separated by '.'"):
        LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), dependencies)


def test_invalid_dependency_namespace(galaxy_info):
    dependencies = ["-invalid-username.notre"]

    with pytest.raises(ValueError, match="dependency namespace "):
        LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), dependencies)


def test_invalid_dependency_name(galaxy_info):
    dependencies = ["notre.1invalid_name"]

    with pytest.raises(ValueError, match="dependency name "):
        LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), dependencies)


def test_self_dependency(galaxy_info):
    dependencies = ["someone.my_role"]
    with pytest.raises(ValueError, match="cannot depend on itself"):
        LegacyImportResult(
            "someone",
            "my_role",
            LegacyMetadata(LegacyGalaxyInfo(**galaxy_info), dependencies),
            "README.md",
            "",
        )