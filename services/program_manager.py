# src/services/program_manager.py

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Set
import logging
import shutil
from dataclasses import dataclass
from enum import Enum

class ProgramType(Enum):
    """Types of external programs used"""
    VEGA = "vega"
    AMMP = "ammp"
    MOPAC = "mopac"

@dataclass
class ProgramInfo:
    """Information about an external program"""
    name: str
    executable: str
    required: bool = True
    version_flag: Optional[str] = None
    working_dir: Optional[Path] = None

class ProgramManager:
    """Manager for external program dependencies"""
    
    def __init__(self, base_dir: Path):
        """
        Initialize program manager.
        
        Args:
            base_dir: Base directory for program files
        """
        self.base_dir = base_dir
        self.programs_dir = base_dir / 'programs'
        self.logger = logging.getLogger("program_manager")
        
        # Define program information
        self.program_info: Dict[ProgramType, ProgramInfo] = {
            ProgramType.VEGA: ProgramInfo(
                name="VEGA ZZ",
                executable=self._get_exe_name("vega"),
                version_flag="-v"
            ),
            ProgramType.AMMP: ProgramInfo(
                name="AMMP",
                executable=self._get_exe_name("Ammp"),
                version_flag=None
            ),
            ProgramType.MOPAC: ProgramInfo(
                name="MOPAC2016",
                executable=self._get_exe_name("MOPAC2016"),
                version_flag=None
            )
        }
        
        # Track temporary files
        self._temp_files: Set[Path] = set()
        
        self._verify_programs()

    def _verify_programs(self):
        """Verify all required programs are available"""
        missing_programs = []
        
        for prog_type, info in self.program_info.items():
            exe_path = self.get_program_path(prog_type)
            
            if not exe_path.exists():
                if info.required:
                    missing_programs.append(info.name)
                self.logger.warning(f"{info.name} not found at {exe_path}")
            else:
                self.logger.info(f"Found {info.name} at {exe_path}")
                info.working_dir = exe_path.parent
                
        if missing_programs:
            msg = (
                "Required programs not found:\n"
                f"- {', '.join(missing_programs)}\n"
                f"Please ensure they are installed in {self.programs_dir}"
            )
            raise RuntimeError(msg)

    def get_program_path(self, program_type: ProgramType) -> Path:
        """Get path to program executable."""
        info = self.program_info[program_type]
        return self.programs_dir / program_type.value / info.executable

    def get_working_dir(self, program_type: ProgramType) -> Optional[Path]:
        """Get program working directory."""
        return self.program_info[program_type].working_dir

    def verify_program(self, program_type: ProgramType) -> bool:
        """
        Verify specific program is available and executable.
        
        Args:
            program_type: Type of program to verify
            
        Returns:
            bool: True if program is available and executable
        """
        try:
            exe_path = self.get_program_path(program_type)
            if not exe_path.exists() or not exe_path.is_file():
                self.logger.warning(
                    f"{program_type.value} not found at {exe_path}"
                )
                return False
                
            # For Windows, just check file existence
            if sys.platform == 'win32':
                return True
                
            # For Unix, check execute permission
            if not os.access(str(exe_path), os.X_OK):
                self.logger.warning(
                    f"{program_type.value} at {exe_path} is not executable"
                )
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error verifying {program_type.value}: {str(e)}"
            )
            return False

    def get_vega_path(self) -> Path:
        """Get path to VEGA executable."""
        return self.programs_dir / 'vega' / self._get_exe_name("vega")

    def get_vega_dir(self) -> Path:
        """Get VEGA working directory."""
        return self.programs_dir / 'vega'

    def get_ammp_path(self) -> Path:
        """Get path to AMMP executable."""
        return self.programs_dir / 'ammp' / self._get_exe_name("Ammp")

    def get_ammp_dir(self) -> Path:
        """Get AMMP working directory."""
        return self.programs_dir / 'ammp'

    def get_mopac_path(self) -> Path:
        """Get path to MOPAC executable."""
        return self.programs_dir / 'mopac' / self._get_exe_name("MOPAC2016")

    def get_mopac_dir(self) -> Path:
        """Get MOPAC working directory."""
        return self.programs_dir / 'mopac'

    def setup_programs(self) -> List[str]:
        """
        Setup program structure and report missing components.
        
        Returns:
            List[str]: List of missing programs
        """
        missing = []
        
        # Ensure programs directory exists
        self.programs_dir.mkdir(parents=True, exist_ok=True)
        
        # Check each program
        for prog_type, info in self.program_info.items():
            prog_dir = self.programs_dir / prog_type.value
            prog_dir.mkdir(exist_ok=True)
            
            exe_path = prog_dir / info.executable
            if not exe_path.exists() and info.required:
                missing.append(info.name)
                
        return missing

    def cleanup_programs(self):
        """Clean up temporary program files"""
        try:
            # Clean VEGA temporary files
            vega_dir = self.get_vega_dir()
            if vega_dir.exists():
                for pattern in ["*.log", "*.tmp"]:
                    for file in vega_dir.glob(pattern):
                        file.unlink()
                        
            # Clean MOPAC temporary files
            mopac_dir = self.get_mopac_dir()
            if mopac_dir.exists():
                for pattern in ["*.mgf", "*.arc"]:
                    for file in mopac_dir.glob(pattern):
                        file.unlink()
                        
            # Remove tracked temporary files
            for temp_file in self._temp_files:
                if temp_file.exists():
                    if temp_file.is_file():
                        temp_file.unlink()
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
            self._temp_files.clear()
                        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def track_temp_file(self, file_path: Path):
        """Track a temporary file for cleanup."""
        self._temp_files.add(file_path)

    @staticmethod
    def _get_exe_name(base_name: str) -> str:
        """Add .exe extension on Windows."""
        if sys.platform == "win32":
            return f"{base_name}.exe"
        return base_name