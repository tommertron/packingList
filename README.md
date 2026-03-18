# Packing List

A personal packing list tool that pushes categorized items to [Todoist](https://todoist.com). Comes with a web UI and a CLI script.

## Features

- Web UI to manage list categories/items and send to Todoist with one click
- CLI (`pack.sh`) to answer trip questions in the terminal and push directly
- Tag-based filtering — items are tagged (e.g. `camping`, `work`, `airplane`) so only relevant ones are sent per trip

## Setup

### 1. Clone the repo

```bash
git clone git@github.com:tommertron/packingList.git
cd packingList
```

### 2. Create your `.env` file

```bash
cp .env.example .env   # or just create it manually
```

Add your Todoist API key:

```
TODOIST_API_KEY=your_api_key_here
```

Get your API key from [Todoist Settings → Integrations → Developer](https://app.todoist.com/app/settings/integrations/developer).

### 3. Set up your packing list

Copy the template to create your personal list:

```bash
cp packing.template.json packing.json
```

`packing.json` is gitignored — edits you make there (adding personal items, categories, etc.) won't be overwritten when you pull updates.

## Running the Web UI

```bash
python3 server.py
```

Opens at [http://localhost:8420](http://localhost:8420). You can change the port:

```bash
python3 server.py 9000
```

## Running the CLI

```bash
python3 pack.sh
```

Asks you a series of yes/no questions about your trip, then pushes the filtered list as a nested Todoist task.

## Customizing Your List

Edit `packing.json` (your local copy) directly in the web UI or with any text editor. The JSON structure:

```json
{
  "questions": [
    { "id": "camping", "label": "Camping?" }
  ],
  "categories": [
    {
      "name": "Category Name",
      "tags": ["always"],
      "items": ["Item 1", "Item 2"]
    }
  ]
}
```

- `tags: ["always"]` — always included
- Any other tag must match a question `id` to be included

## Requirements

- Python 3 (stdlib only, no packages needed)
- A Todoist account with API access
