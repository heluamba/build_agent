FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

# Copiar apenas os arquivos de dependências primeiro
COPY pyproject.toml uv.lock* ./

VOLUME [ "/data" ]

RUN uv sync

COPY . .

CMD ["uv", "run", "main.py"]
