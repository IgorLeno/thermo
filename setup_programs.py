import os
import sys
import subprocess
import requests
import zipfile
import logging
import platform
import shutil
import yaml
from pathlib import Path
import tempfile

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("setup_programs")

# --- Constantes para download e instalação ---
CREST_URL = "https://github.com/grimme-lab/crest/archive/refs/heads/master.zip"
OPENBABEL_WIN_URL = "https://github.com/openbabel/openbabel/releases/download/openbabel-3-1-1/OpenBabel-3.1.1-x64.zip"
MOPAC_INFO_URL = "http://openmopac.net/MOPAC2016.html"  # URL informativa sobre o MOPAC

PROGRAM_PATHS = {
    "crest": Path("./programs/crest"),
    "openbabel": Path("./programs/OpenBabel"),
    "mopac": Path("./programs/MOPAC"),
}

def is_admin():
    """Verifica se o script está sendo executado com privilégios de administrador."""
    try:
        if platform.system() == "Windows":
            return subprocess.run(["net", "session"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
        else:
            return os.geteuid() == 0
    except:
        return False

def download_file(url, destination):
    """Faz o download de um arquivo a partir de uma URL e salva no destino."""
    try:
        logger.info(f"Baixando de {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                downloaded += len(chunk)
                
                # Exibe progresso
                if total_size > 0:
                    progress = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * progress}{' ' * (50 - progress)}] {downloaded}/{total_size} bytes")
                    sys.stdout.flush()
        
        if total_size > 0:
            sys.stdout.write("\n")
        
        logger.info(f"Download concluído: {destination}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao fazer o download de {url}: {e}")
        return False

def check_wsl():
    """Verifica se o WSL está instalado e a versão do Ubuntu está disponível."""
    try:
        result = subprocess.run(["wsl", "--list"], capture_output=True, text=True)
        
        if "Ubuntu" in result.stdout:
            logger.info("WSL com Ubuntu encontrado!")
            return True
        else:
            logger.warning("WSL instalado, mas Ubuntu não encontrado!")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar WSL: {e}")
        return False

def install_crest():
    """Faz o download e instala o CREST."""
    logger.info("Iniciando instalação do CREST...")
    
    if not check_wsl():
        logger.warning("WSL não encontrado ou Ubuntu não instalado! O CREST requer WSL com Ubuntu.")
        logger.info("Por favor, instale o WSL e Ubuntu usando: wsl --install -d Ubuntu")
        return False
    
    # Cria diretório se não existir
    os.makedirs(PROGRAM_PATHS["crest"], exist_ok=True)
    
    # Baixa o arquivo ZIP do CREST
    crest_zip_path = PROGRAM_PATHS["crest"] / "crest-master.zip"
    if not download_file(CREST_URL, crest_zip_path):
        return False

    # Extrai o arquivo ZIP
    try:
        logger.info(f"Extraindo {crest_zip_path}...")
        with zipfile.ZipFile(crest_zip_path, 'r') as zip_ref:
            zip_ref.extractall(PROGRAM_PATHS["crest"])
        logger.info("Extração concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao extrair arquivo ZIP do CREST: {e}")
        return False
    
    # Exibe instruções para instalação no WSL
    logger.info("\n=== Instruções para concluir a instalação do CREST no WSL ===")
    logger.info("1. Abra o terminal WSL (Ubuntu)")
    logger.info("2. Instale o miniconda:")
    logger.info("   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh")
    logger.info("   bash Miniconda3-latest-Linux-x86_64.sh")
    logger.info("3. Crie e configure o ambiente conda para o CREST:")
    logger.info("   conda create -n crest_env")
    logger.info("   conda activate crest_env")
    logger.info("   conda install -c conda-forge xtb crest")
    logger.info("4. Atualize o caminho do CREST no arquivo config.yaml para:")
    logger.info("   \\\\wsl.localhost\\Ubuntu\\home\\SEU_USUÁRIO\\miniconda3\\envs\\crest_env\\bin\\crest")
    logger.info("=== Fim das instruções ===\n")
    
    return True

def install_openbabel():
    """Baixa e configura o OpenBabel."""
    logger.info("Iniciando download do OpenBabel...")
    
    # Verifica se estamos no Windows
    if platform.system() != "Windows":
        logger.warning("O download automático do OpenBabel só é suportado no Windows.")
        logger.info("Por favor, instale o OpenBabel manualmente conforme as instruções no README.")
        return False
    
    # Cria diretório se não existir
    os.makedirs(PROGRAM_PATHS["openbabel"], exist_ok=True)
    
    # Baixa o arquivo ZIP do OpenBabel
    openbabel_zip_path = PROGRAM_PATHS["openbabel"] / "OpenBabel-3.1.1-x64.zip"
    if not download_file(OPENBABEL_WIN_URL, openbabel_zip_path):
        return False

    # Extrai o arquivo ZIP
    try:
        logger.info(f"Extraindo {openbabel_zip_path}...")
        with zipfile.ZipFile(openbabel_zip_path, 'r') as zip_ref:
            zip_ref.extractall(PROGRAM_PATHS["openbabel"])
        logger.info("Extração concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao extrair arquivo ZIP do OpenBabel: {e}")
        return False
    
    # Exibe mensagem sobre a instalação
    logger.info("\n=== Informações sobre o OpenBabel ===")
    logger.info("O OpenBabel foi baixado e extraído com sucesso.")
    logger.info(f"Diretório de instalação: {PROGRAM_PATHS['openbabel'].absolute()}")
    logger.info("Para adicionar o OpenBabel ao PATH do sistema:")
    logger.info("1. Abra as configurações do sistema")
    logger.info("2. Vá para Variáveis de Ambiente")
    logger.info("3. Adicione o caminho ao diretório bin do OpenBabel na variável PATH")
    logger.info("=== Fim das informações ===\n")
    
    return True

def mopac_instructions():
    """Fornece instruções para download e instalação do MOPAC."""
    logger.info("\n=== Instruções para obter e instalar o MOPAC ===")
    logger.info("O MOPAC requer download e instalação manual:")
    logger.info(f"1. Visite: {MOPAC_INFO_URL}")
    logger.info("2. Preencha o formulário para solicitar uma licença acadêmica gratuita")
    logger.info("3. Você receberá um e-mail com instruções para download")
    logger.info("4. Instale o MOPAC seguindo as instruções no e-mail")
    logger.info("5. Atualize o caminho do MOPAC no arquivo config.yaml")
    logger.info("=== Fim das instruções ===\n")

def verify_installations():
    """Verifica se os programas foram instalados corretamente."""
    logger.info("Verificando instalações...")
    
    success = True
    
    for program, path in PROGRAM_PATHS.items():
        if path.exists():
            logger.info(f"✓ Diretório de {program} encontrado: {path.absolute()}")
        else:
            logger.warning(f"✗ Diretório de {program} não encontrado: {path.absolute()}")
            success = False
    
    # Verifica os programas no PATH
    executables = {
        "OpenBabel": "obabel",
        "MOPAC": "MOPAC2016.exe",
        "WSL": "wsl"
    }
    
    for name, cmd in executables.items():
        path = shutil.which(cmd)
        if path:
            logger.info(f"✓ {name} encontrado no PATH: {path}")
        else:
            logger.warning(f"✗ {name} não encontrado no PATH!")
            if name != "WSL":  # WSL é apenas um aviso, não um erro
                success = False
    
    return success

def update_config_paths():
    """Atualiza o arquivo de configuração com os caminhos dos programas encontrados."""
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        logger.warning(f"Arquivo de configuração {config_file} não encontrado.")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Detecta os caminhos dos programas
        openbabel_path = shutil.which("obabel")
        mopac_path = shutil.which("MOPAC2016.exe") or shutil.which("MOPAC2023.exe")
        
        # Atualiza apenas se encontrados
        if openbabel_path:
            config["programs"]["openbabel_path"] = openbabel_path
        
        if mopac_path:
            config["programs"]["mopac_path"] = mopac_path
        
        # Escreve o arquivo atualizado
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Arquivo de configuração {config_file} atualizado com caminhos dos programas.")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar arquivo de configuração: {e}")
        return False

def check_and_setup_wsl():
    """Verifica a configuração do WSL e fornece orientações se necessário."""
    if platform.system() != "Windows":
        logger.info("Não está executando no Windows, ignorando configuração do WSL.")
        return False
    
    try:
        # Verifica se o WSL está instalado
        wsl_check = subprocess.run(["wsl", "--status"], 
                                   capture_output=True, 
                                   text=True)
        
        if wsl_check.returncode != 0:
            logger.warning("WSL não parece estar instalado ou configurado corretamente.")
            logger.info("Para instalar o WSL no Windows 10/11, execute como administrador:")
            logger.info("wsl --install -d Ubuntu")
            return False
        
        # Verifica se o Ubuntu está instalado
        distro_check = subprocess.run(["wsl", "--list"], 
                                     capture_output=True, 
                                     text=True)
        
        if "Ubuntu" not in distro_check.stdout:
            logger.warning("Ubuntu não encontrado no WSL.")
            logger.info("Para instalar o Ubuntu no WSL, execute:")
            logger.info("wsl --install -d Ubuntu")
            return False
        
        # Verifica a versão do WSL
        if "WSL 2" not in wsl_check.stdout and "Versão: 2" not in wsl_check.stdout:
            logger.warning("Você parece estar usando o WSL 1. Recomendamos atualizar para o WSL 2.")
            logger.info("Para converter para WSL 2, execute:")
            logger.info("wsl --set-version Ubuntu 2")
            return True  # Return True anyway, this is just a recommendation
        
        logger.info("WSL 2 com Ubuntu encontrado e configurado corretamente!")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar o WSL: {e}")
        return False

def main():
    """Função principal para instalação dos programas."""
    logger.info("=== Iniciando configuração de programas para Grimme Thermo ===\n")
    
    # Verifica se é Windows
    if platform.system() != "Windows":
        logger.warning("Este script foi projetado principalmente para Windows. Algumas funcionalidades podem não funcionar corretamente.")
    
    # Verifica configuração do WSL
    check_and_setup_wsl()
    
    # Oferece menu de opções
    print("\nEscolha quais programas configurar:")
    print("1. Todos os programas")
    print("2. Apenas CREST (requer WSL)")
    print("3. Apenas OpenBabel")
    print("4. Apenas instruções para MOPAC")
    print("5. Verificar instalações existentes")
    print("6. Atualizar caminhos no config.yaml")
    print("7. Sair")
    
    choice = input("\nEscolha uma opção (1-7): ")
    
    if choice == "1":
        install_crest()
        install_openbabel()
        mopac_instructions()
        verify_installations()
        update_config_paths()
    elif choice == "2":
        install_crest()
    elif choice == "3":
        install_openbabel()
    elif choice == "4":
        mopac_instructions()
    elif choice == "5":
        verify_installations()
    elif choice == "6":
        update_config_paths()
    elif choice == "7":
        logger.info("Saindo sem configurar programas.")
        return
    else:
        logger.warning("Opção inválida!")
        return
    
    logger.info("\n=== Configuração de programas concluída! ===")
    logger.info("Lembre-se de verificar o arquivo config.yaml e ajustar os caminhos conforme necessário.")

if __name__ == "__main__":
    main()
