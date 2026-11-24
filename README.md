# MongoDB Rate Limiter

This is a simple rate limiter built using Python, Flask and MongoDB.

It allows each client to make **5 API requests per minute**. After the limit is reached, additional requests are blocked until the next time window.

## Requirements

- Python 3.9 or newer
- MongoDB Community Server, running locally

No sample data needs to be imported. The application creates its database, collection and indexes automatically.

## Running on Windows

1. Download the repository ZIP from GitHub and extract it.
2. Open the extracted project folder.
3. Type `powershell` in File Explorer's address bar and press Enter.
4. Run these commands:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Make sure MongoDB Server is running before starting the application.

## Running on macOS

1. Download and extract the repository.
2. Open Terminal in the project folder.
3. Run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Make sure MongoDB Server is running.

## Testing

Open another terminal while the application is running.

**Windows:**

```powershell
curl.exe -i -H "X-Client-ID: test-user" http://127.0.0.1:5000/api/data
```

**macOS:**

```bash
curl -i -H "X-Client-ID: test-user" http://127.0.0.1:5000/api/data
```

Run the command six times quickly within the same minute.

Expected result:

- First five requests: HTTP 200
- Sixth request: HTTP 429
- Next time window: Requests are allowed again

Different client IDs have independent request limits.

## How It Works

The application uses the Fixed-Window Counter algorithm.

Flask receives API requests, and MongoDB stores each client's request count for the current time window. Each request increments the counter atomically.

The database uses a unique compound index for client and time window, along with a TTL index for cleaning up older records.

## Technologies

- Python
- Flask
- MongoDB
- PyMongo

This project is intended for local educational demonstration. The client ID header is for testing and is not an authenticated identity.

To stop the application, press Ctrl+C in the terminal running Flask.
