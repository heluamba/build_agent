# build_agent

A CLI tool that accepts a coding task, selects predefined actions, and runs them in sequence until completion or failure.

## Run

```bash
python /home/runner/work/build_agent/build_agent/build_agent.py "scan directory and read README.md"
```

## Predefined actions

- Scan files in a directory
- Read a file's contents
- Overwrite a file's contents
- Execute Python on a file
