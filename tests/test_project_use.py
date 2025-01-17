from click.testing import CliRunner

from weni_cli.cli import project


def test_project_use(mocker):
    runner = CliRunner()
    with runner.isolated_filesystem():
        store_set_patch = mocker.patch("weni_cli.store.Store.set", return_value=None)
        result = runner.invoke(project, ["use", "123456"])

        assert store_set_patch.call_count == 1
        assert result.exit_code == 0
        assert result.output == "Project 123456 set as default\n"
