# src/services/cleanup_service.py

import logging
import shutil
from pathlib import Path
from typing import Set, Dict, List, Optional
from enum import Enum

class CleanupScope(Enum):
    """Define the scope of cleanup operations"""
    TEMPORARY = "temporary"  # Only temporary files
    INTERMEDIATE = "intermediate"  # Temporary + intermediate files
    ALL = "all"  # Complete cleanup including outputs

class CleanupService:
    """Service responsible for cleaning up files after calculations"""
    
    def __init__(self, base_dir: Path):
        """
        Initialize cleanup service.
        
        Args:
            base_dir: Base directory containing all project folders
        """
        self.base_dir = base_dir
        self.logger = logging.getLogger("cleanup_service")
        
        # Track temporary and protected files
        self._temp_files: Set[Path] = set()
        self._protected_files: Set[Path] = set()
        
        # Define cleanup patterns for each directory
        self.cleanup_patterns = {
            'vega': ['*.log', '*.tmp', '*.sdf', '*.amp'],
            'ammp': ['*_script.amp', '*.amp', '*.pdb'],
            'mopac': ['*.mop', '*.mgf', '*.pdb', '*.arc']
        }
        
        # Define protected file patterns
        self.protected_patterns = {
            'rep_sdf': ['*.sdf'],
            'rep_tgroups': ['*.amp'],
            'rep_tjump': ['*_tjump.amp'],
            'rep_mopac': ['*.arc', '*_hof.pdb'],
            'final_molecules/out': ['*.out']
        }
        
    def register_temp_file(self, file_path: Path):
        """Register a temporary file for cleanup"""
        self._temp_files.add(file_path)
        self.logger.debug(f"Registered temporary file: {file_path}")
        
    def protect_file(self, file_path: Path):
        """Mark a file as protected from cleanup"""
        self._protected_files.add(file_path)
        self.logger.debug(f"Protected file from cleanup: {file_path}")
        
    def cleanup_calculation(self, molecule_name: str, scope: CleanupScope = CleanupScope.TEMPORARY):
        """
        Clean up files from a specific calculation with improved program directory cleaning.
        
        Args:
            molecule_name: Name of molecule
            scope: Cleanup scope (TEMPORARY, INTERMEDIATE, or ALL)
        """
        try:
            self.logger.info(f"Starting cleanup for {molecule_name}")
            
            # Define program directories to clean
            program_dirs = {
                'vega': self.base_dir / 'programs/vega',
                'ammp': self.base_dir / 'programs/ammp',
                'mopac': self.base_dir / 'programs/mopac'
            }
            
            # Define patterns for each program directory
            cleanup_patterns = {
                'vega': [
                    f"{molecule_name}*.sdf",
                    f"{molecule_name}*.amp",
                    f"{molecule_name}*.log",
                    f"{molecule_name}*.tmp",
                    "*.log",
                    "*.tmp"
                ],
                'ammp': [
                    f"{molecule_name}*.amp",
                    f"{molecule_name}*.pdb",
                    f"{molecule_name}*_script.amp"
                ],
                'mopac': [
                    f"{molecule_name}*.mop",
                    f"{molecule_name}*.mgf",
                    f"{molecule_name}*.arc",
                    f"{molecule_name}*.pdb",
                    "*.mgf"  # Arquivos temporários do MOPAC
                ]
            }
            
            # Clean each program directory
            for prog_name, prog_dir in program_dirs.items():
                if prog_dir.exists():
                    patterns = cleanup_patterns[prog_name]
                    for pattern in patterns:
                        for file_path in prog_dir.glob(pattern):
                            if file_path not in self._protected_files:
                                try:
                                    file_path.unlink()
                                    self.logger.debug(f"Removed {file_path}")
                                except Exception as e:
                                    self.logger.warning(f"Failed to remove {file_path}: {str(e)}")
                                    
            # Clean registered temporary files
            for file_path in self._temp_files.copy():
                if molecule_name in file_path.name and file_path.exists():
                    try:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                        self._temp_files.remove(file_path)
                        self.logger.debug(f"Removed temporary file: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove {file_path}: {str(e)}")
                        
            # Additional cleanup based on scope
            if scope in [CleanupScope.INTERMEDIATE, CleanupScope.ALL]:
                self._cleanup_intermediate_files(molecule_name)
                
            if scope == CleanupScope.ALL:
                self._cleanup_output_files(molecule_name)
                
            self.logger.info(f"Completed cleanup for {molecule_name}")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed for {molecule_name}: {str(e)}")
            raise
 
    def verify_cleanup(self, molecule_name: str) -> List[Path]:
        """
        Verify if any files related to the molecule still exist in program directories.
        
        Args:
            molecule_name: Name of molecule
            
        Returns:
            List[Path]: List of files that should have been cleaned
        """
        remaining_files = []
        
        program_dirs = [
            self.base_dir / 'programs/vega',
            self.base_dir / 'programs/ammp',
            self.base_dir / 'programs/mopac'
        ]
        
        for prog_dir in program_dirs:
            if prog_dir.exists():
                # Check for any files containing molecule name
                for file_path in prog_dir.glob(f"*{molecule_name}*"):
                    if file_path not in self._protected_files:
                        remaining_files.append(file_path)
                        
                # Check for common temporary files
                for pattern in ["*.log", "*.tmp", "*.mgf"]:
                    for file_path in prog_dir.glob(pattern):
                        if file_path not in self._protected_files:
                            remaining_files.append(file_path)
                            
        return remaining_files 
            
    def _cleanup_program_dirs(self, molecule_name: str):
        """Clean up program directories using defined patterns"""
        for program_dir, patterns in self.cleanup_patterns.items():
            dir_path = self.base_dir / program_dir
            if dir_path.exists():
                for pattern in patterns:
                    for file_path in dir_path.glob(f"{molecule_name}{pattern}"):
                        if file_path not in self._protected_files:
                            try:
                                file_path.unlink()
                                self.logger.debug(f"Removed {file_path}")
                            except Exception as e:
                                self.logger.warning(f"Failed to remove {file_path}: {str(e)}")
                                
    def _cleanup_temp_files(self, molecule_name: str):
        """Clean up registered temporary files"""
        for file_path in self._temp_files.copy():
            if molecule_name in file_path.name and file_path.exists():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    self._temp_files.remove(file_path)
                    self.logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
                    
    def _cleanup_intermediate_files(self, molecule_name: str):
        """Clean up intermediate calculation files"""
        intermediate_dirs = ['rep_tgroups', 'rep_tjump', 'rep_mopac']
        for dir_name in intermediate_dirs:
            dir_path = self.base_dir / 'repository' / dir_name
            if dir_path.exists():
                for file_path in dir_path.glob(f"{molecule_name}*"):
                    if file_path not in self._protected_files:
                        try:
                            file_path.unlink()
                            self.logger.debug(f"Removed intermediate file: {file_path}")
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to remove intermediate file {file_path}: {str(e)}"
                            )
                            
    def _cleanup_output_files(self, molecule_name: str):
        """Clean up final output files"""
        output_dirs = ['final_molecules/out', 'final_molecules']
        for dir_name in output_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.glob(f"{molecule_name}*"):
                    if file_path not in self._protected_files:
                        try:
                            file_path.unlink()
                            self.logger.debug(f"Removed output file: {file_path}")
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to remove output file {file_path}: {str(e)}"
                            )
                            
    def protect_important_files(self, molecule_name: str):
        """Protect important files from cleanup based on patterns"""
        for dir_name, patterns in self.protected_patterns.items():
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                for pattern in patterns:
                    for file_path in dir_path.glob(f"{molecule_name}{pattern}"):
                        self.protect_file(file_path)
                        
    def cleanup_all(self, scope: CleanupScope = CleanupScope.TEMPORARY):
        """Clean up all unprotected files in program directories"""
        try:
            self.logger.info(f"Starting complete cleanup with scope {scope.value}")
            
            # Clean program directories
            for program_dir, patterns in self.cleanup_patterns.items():
                dir_path = self.base_dir / program_dir
                if dir_path.exists():
                    for pattern in patterns:
                        for file_path in dir_path.glob(pattern):
                            if file_path not in self._protected_files:
                                try:
                                    file_path.unlink()
                                    self.logger.debug(f"Removed {file_path}")
                                except Exception as e:
                                    self.logger.warning(
                                        f"Failed to remove {file_path}: {str(e)}"
                                    )
                                    
            # Clean all temporary files
            self._cleanup_all_temp_files()
            
            # Additional cleanup based on scope
            if scope in [CleanupScope.INTERMEDIATE, CleanupScope.ALL]:
                self._cleanup_all_intermediate_files()
                
            if scope == CleanupScope.ALL:
                self._cleanup_all_output_files()
                
            self.logger.info("Completed complete cleanup")
            
        except Exception as e:
            self.logger.error(f"Complete cleanup failed: {str(e)}")
            raise
            
    def _cleanup_all_temp_files(self):
        """Clean up all registered temporary files"""
        for file_path in self._temp_files.copy():
            if file_path.exists():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    self._temp_files.remove(file_path)
                    self.logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
                    
    def _cleanup_all_intermediate_files(self):
        """Clean up all intermediate calculation files"""
        intermediate_dirs = ['rep_tgroups', 'rep_tjump', 'rep_mopac']
        for dir_name in intermediate_dirs:
            dir_path = self.base_dir / 'repository' / dir_name
            if dir_path.exists():
                for file_path in dir_path.glob("*"):
                    if file_path not in self._protected_files:
                        try:
                            file_path.unlink()
                            self.logger.debug(f"Removed intermediate file: {file_path}")
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to remove intermediate file {file_path}: {str(e)}"
                            )
                            
    def _cleanup_all_output_files(self):
        """Clean up all output files"""
        output_dirs = ['final_molecules/out', 'final_molecules']
        for dir_name in output_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.glob("*"):
                    if file_path not in self._protected_files:
                        try:
                            file_path.unlink()
                            self.logger.debug(f"Removed output file: {file_path}")
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to remove output file {file_path}: {str(e)}"
                            )