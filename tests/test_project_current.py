from click.testing import CliRunner

from weni_cli.cli import project


def test_project_current(mocker):
    runner = CliRunner()
    with runner.isolated_filesystem():
        store_get_patch = mocker.patch("weni_cli.store.Store.get", side_effect=["123456"])
        result = runner.invoke(project, ["current"])

        assert store_get_patch.call_count == 1
        assert result.exit_code == 0
        assert result.output == "Current project: 123456\n"
