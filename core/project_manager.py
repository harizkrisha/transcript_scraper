import os
from typing import List, Tuple

class ProjectManager:
    """
    Handles creation and listing of projects and subprojects under a given root directory.
    """

    def __init__(self, output_root: str):
        self.output_root = output_root
        os.makedirs(self.output_root, exist_ok=True)

    def get_projects(self) -> List[str]:
        """Return a sorted list of project names (subdirectories of output_root)."""
        return sorted(
            name for name in os.listdir(self.output_root)
            if os.path.isdir(os.path.join(self.output_root, name))
        )

    def get_subprojects(self, project: str) -> List[str]:
        """Return a sorted list of subproject names under a given project."""
        proj_dir = os.path.join(self.output_root, project)
        if not os.path.isdir(proj_dir):
            return []
        return sorted(
            name for name in os.listdir(proj_dir)
            if os.path.isdir(os.path.join(proj_dir, name))
        )

    def create_project(self, project: str) -> Tuple[bool, str]:
        """Create a new project directory."""
        path = os.path.join(self.output_root, project)
        if os.path.exists(path):
            return False, f"Project '{project}' already exists."
        try:
            os.makedirs(path)
            return True, f"Project '{project}' created."
        except Exception as e:
            return False, f"Failed to create project: {e}"

    def create_subproject(self, project: str, subproject: str) -> Tuple[bool, str]:
        """Create a new subproject directory under an existing project."""
        proj_dir = os.path.join(self.output_root, project)
        if not os.path.isdir(proj_dir):
            return False, f"Project '{project}' does not exist."
        sub_dir = os.path.join(proj_dir, subproject)
        if os.path.exists(sub_dir):
            return False, f"Subproject '{subproject}' already exists under '{project}'."
        try:
            os.makedirs(sub_dir)
            return True, f"Subproject '{subproject}' created under '{project}'."
        except Exception as e:
            return False, f"Failed to create subproject: {e}"
