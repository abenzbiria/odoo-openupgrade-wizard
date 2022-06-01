from . import cli_runner_invoke, move_to_test_folder


def test_cli_estimate_workload():
    move_to_test_folder()

    cli_runner_invoke(
        [
            "--log-level=DEBUG",
            "estimate-workload",
        ]
    )
    # TODO, write test
