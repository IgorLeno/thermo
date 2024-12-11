from dataclasses import dataclass
from typing import Optional

@dataclass
class CalculationParameters:
    """
    Armazena os parâmetros para os cálculos com CREST e xTB.
    """
    n_threads: int = 1
    crest_method: str = "gfn2"  # Pode ser "gfn1", "gfn2" ou "gfnff"
    electronic_temperature: float = 300.0 # em Kelvin
    solvent: Optional[str] = None

    def crest_command(self, xyz_file: str) -> list:
        """Retorna o comando para executar o CREST."""
        crest_methods = {
            "gfn1": "--gfn 1",
            "gfn2": "--gfn 2",
            "gfnff": "--gfnff"
        }
        command = [
            "crest",
            xyz_file,
            "--chrg", "0",
            "--uhf", "0",
            "-T", str(self.n_threads),
            crest_methods.get(self.crest_method, "--gfn 2")
        ]
        if self.solvent:
            command.extend(["--solv", self.solvent])
        return command

    def xtb_command(self, xyz_file: str, task: str) -> list:
        """Retorna o comando para executar o xTB."""
        command = [
            "xtb",
            xyz_file,
            f"--{task}",
            "--chrg", "0",
            "--uhf", "0",
            "-T", str(self.n_threads)
        ]

        if task == 'opt' and self.electronic_temperature:
            command.extend(["--etemp", str(self.electronic_temperature)])

        if self.solvent:
            command.extend(["--gbsa", self.solvent])
        return command