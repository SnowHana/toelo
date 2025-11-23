# Toelo (formerly Footy)

Football data analysis and ELO rating system.

## Setup

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    poetry install
    ```
3.  **Environment Configuration**:
    Copy `.env.example` to `.env` and update with your database credentials.
    ```bash
    cp .env.example .env
    ```

## Usage

### CLI Tool
Run the command-line interface:
```bash
python -m toelo.clt_main
```

### Streamlit App
Run the frontend dashboard:
```bash
streamlit run src/toelo/frontend/main.py
```

## Testing
Run unit tests:
```bash
python -m unittest discover tests
```
