import os
import sys
import subprocess

def run_cmd(cmd):
    print(f"A executar: {cmd}")
    subprocess.check_call(cmd, shell=True)

def main():
    # Detect platform
    is_win = sys.platform.startswith("win")
    
    # Path to pip and python inside venv
    venv_bin = "venv\\Scripts" if is_win else "venv/bin"
    python_exe = os.path.join(venv_bin, "python.exe" if is_win else "python")
    pip_exe = os.path.join(venv_bin, "pip.exe" if is_win else "pip")
    
    if not os.path.exists(python_exe):
        # Fallback to system python if venv doesn't exist
        python_exe = "python"
        pip_exe = "pip"
        
    print("--- 1. Instalar PyInstaller ---")
    run_cmd(f'"{pip_exe}" install pyinstaller')
    
    print("\n--- 2. Compilar Aplicação ---")
    
    # Ensure sounds directory exists before bundling
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
        print("Criada pasta 'sounds' vazia.")
        
    # PyInstaller data separator is platform dependent (';' on Windows, ':' on macOS/Linux)
    sep = ";" if is_win else ":"
    
    # Build command
    # --noconsole hides the command prompt window behind the GUI
    # --onefile packages everything into a single executable file
    cmd = f'"{python_exe}" -m PyInstaller --clean --noconsole --onefile --add-data "sounds{sep}sounds" --name="KarateManager" main.py'
    run_cmd(cmd)
    
    print("\n--- 3. Concluído! ---")
    if is_win:
        print("O seu executável está na pasta: dist\\KarateManager.exe")
    else:
        print("O seu executável está na pasta: dist/KarateManager")
        
if __name__ == "__main__":
    main()
