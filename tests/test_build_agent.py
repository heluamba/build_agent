import tempfile
import unittest
from pathlib import Path

from build_agent import BuildAgent


class BuildAgentTests(unittest.TestCase):
    def test_tool_functions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = BuildAgent(workspace=str(workspace))

            data_file = workspace / "sample.txt"
            write_result = agent.overwrite_file(str(data_file), "hello world")
            self.assertTrue(write_result.success)

            read_result = agent.read_file(str(data_file))
            self.assertTrue(read_result.success)
            self.assertEqual(read_result.output, "hello world")

            scan_result = agent.scan_directory(str(workspace))
            self.assertTrue(scan_result.success)
            self.assertIn("sample.txt", scan_result.output)

    def test_run_task_loops_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            script_path = workspace / "script.py"
            script_path.write_text("print('ok')", encoding="utf-8")

            agent = BuildAgent(workspace=str(workspace), max_steps=5)
            task = f"scan the directory and read {script_path} and execute {script_path}"

            results = agent.run_task(task)

            self.assertEqual([r.name for r in results], ["scan_directory", "read_file", "run_python_file"])
            self.assertTrue(all(r.success for r in results))


if __name__ == "__main__":
    unittest.main()
