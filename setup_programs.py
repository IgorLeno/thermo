import os
import subprocess
import requests
import zipfile
from pathlib import Path

# --- Constantes para download e instalação ---
CREST_URL = "https://github.com/grimme-lab/crest/archive/refs/heads/master.zip"
XTB_URL = "https://github.com/grimme-lab/xtb/releases/download/v6.6.1/xtb-6.6.1-windows-x86_64.zip"
OPENBABEL_URL = "https://github.com/openbabel/openbabel/releases/download/openbabel-3-1-1/OpenBabel-3.1.1-Windows-x86_64.exe"
PROGRAM_PATHS = {
    "crest": Path("./programs/crest"),
    "xtb": Path("./programs/xtb"),
    "openbabel": Path("./programs/OpenBabel"),
}

def download_file(url, destination):
    """Faz o download de um arquivo a partir de uma URL e salva no destino."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download concluído: {destination}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer o download de {url}: {e}")

def install_crest():
    """Faz o download e instala o CREST."""
    crest_zip_path = PROGRAM_PATHS["crest"] / "crest-master.zip"
    download_file(CREST_URL, crest_zip_path)

    with zipfile.ZipFile(crest_zip_path, 'r') as zip_ref:
        zip_ref.extractall(PROGRAM_PATHS["crest"])
    print("CREST instalado com sucesso.")

def install_xtb():
    """Faz o download e instala o xTB."""
    xtb_zip_path = PROGRAM_PATHS["xtb"] / "xtb-6.6.1-windows-x86_64.zip"
    download_file(XTB_URL, xtb_zip_path)

    with zipfile.ZipFile(xtb_zip_path, 'r') as zip_ref:
        zip_ref.extractall(PROGRAM_PATHS["xtb"])
    print("xTB instalado com sucesso.")

def install_openbabel():
    """Faz o download e instala o OpenBabel."""
    openbabel_exe_path = PROGRAM_PATHS["openbabel"] / "OpenBabel-3.1.1-Windows-x86_64.exe"
    download_file(OPENBABEL_URL, openbabel_exe_path)

    try:
        subprocess.run([openbabel_exe_path, "/silent"], check=True)
        print("OpenBabel instalado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar o OpenBabel: {e}")

def verify_installations():
    """Verifica se os programas foram instalados corretamente."""
    for program, path in PROGRAM_PATHS.items():
        if not path.exists():
            print(f"Erro: {program} não encontrado em {path}")
            return False
        else:
            print(f"{program} encontrado em: {path}")
    return True

def set_environment_variables():
    """Configura as variáveis de ambiente para os programas."""
    # Adicionar os diretórios dos programas ao PATH
    os.environ["PATH"] += os.pathsep + str(PROGRAM_PATHS["crest"])
    os.environ["PATH"] += os.pathsep + str(PROGRAM_PATHS["xtb"])
    os.environ["PATH"] += os.pathsep + str(PROGRAM_PATHS["openbabel"])

    print("Variáveis de ambiente configuradas.")

if __name__ == "__main__":
    install_crest()
    install_xtb()
    install_openbabel()
    if verify_installations():
        set_environment_variables()
    print("Configuração dos programas concluída.")