import os
import tempfile
import unittest
from pathlib import Path

import yaml

from src.artifacts import update_champion_model
from src.inference import get_latest_model_path


class TestModelGovernance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.original_cwd = Path.cwd()

        (self.repo_root / "config").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "artifacts").mkdir(parents=True, exist_ok=True)

        os.chdir(self.repo_root)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def write_registry(self, data: dict) -> None:
        registry_path = self.repo_root / "config" / "model_registry.yaml"
        with open(registry_path, "w") as file:
            yaml.safe_dump(data, file, sort_keys=False)

    def test_explicit_champion_model_returns_configured_file(self):
        self.write_registry({"champion_model": "model_explicit.pkl"})
        (self.repo_root / "artifacts" / "model_explicit.pkl").touch()

        model_path = get_latest_model_path()

        self.assertEqual(
            model_path,
            str(Path("artifacts") / "model_explicit.pkl")
        )

    def test_explicit_champion_model_raises_when_file_is_missing(self):
        self.write_registry({"champion_model": "model_missing.pkl"})

        with self.assertRaises(FileNotFoundError):
            get_latest_model_path()

    def test_latest_policy_returns_latest_model_artifact(self):
        self.write_registry({"champion_model": "latest"})
        (self.repo_root / "artifacts" / "model_20260316_120000.pkl").touch()
        (self.repo_root / "artifacts" / "model_20260316_130000.pkl").touch()

        model_path = get_latest_model_path()

        self.assertEqual(
            model_path,
            str(Path("artifacts") / "model_20260316_130000.pkl")
        )

    def test_update_champion_model_preserves_existing_registry_keys(self):
        self.write_registry(
            {
                "champion_model": "latest",
                "promotion_mode": "manual",
                "notes": "day11-governance"
            }
        )

        update_champion_model("model_20260316_142039.pkl")

        registry_path = self.repo_root / "config" / "model_registry.yaml"
        with open(registry_path, "r") as file:
            updated_registry = yaml.safe_load(file)

        self.assertEqual(
            updated_registry["champion_model"],
            "model_20260316_142039.pkl"
        )
        self.assertEqual(updated_registry["promotion_mode"], "manual")
        self.assertEqual(updated_registry["notes"], "day11-governance")


if __name__ == "__main__":
    unittest.main()
