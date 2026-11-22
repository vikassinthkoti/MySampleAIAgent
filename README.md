# Agent Template Pack: Weekly Status Report Agent

The starter for **Zero to Live AI Agent on Cloud** (Future Proof India).

A delivery manager pastes a week of rough team notes (stand-ups, Jira lines, emails). The agent sorts every note, gives an overall Red / Amber / Green status, builds a risk and blocker register with owners and dates, checks its own work against three checks, fixes it, and lists the questions to ask the team. You will change it into your own agent on Day 2 and put it online on Day 3. It runs straight away in **demo mode**, with no AI key.

## Day 2: run it on your computer

1. **Copy this project.** Click the green **Use this template** button at the top right of this page, then **Create a new repository**. Name it `my-agent`, keep it **Public**, and click **Create repository**.
2. **Download it.** On your new repository, click the green **Code** button, then **Download ZIP**. Unzip it into a folder on your computer.
3. **Open the folder in the Antigravity app** (the desktop app, not the Antigravity IDE) and paste the prompt from the Studio step. It installs what the project needs and starts it. If you prefer to type the commands yourself, run these in a terminal inside the folder:

   ```
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

4. **Open the address it prints** (it starts with `localhost`). Press **Load a sample week**, then **Write my report**.

### Use a real AI model

1. Get a key from an AI provider (Google Gemini has a free tier).
2. Copy `.streamlit/secrets.toml.example` to a new file `.streamlit/secrets.toml`. Paste your key and your provider's two lines into it.
3. Restart the project. The green box now says it is using a real model.

`.streamlit/secrets.toml` stays on your computer. It is ignored by Git, and you must never upload it to GitHub.

### Make it yours

| File | What it is | What you do |
|---|---|---|
| `prompts.py` | the agent's job description | rewrite it in your own words |
| `app.py` | the screen people see | improve it |
| `sample_updates.txt` | a sample week of notes | replace with your own samples |
| `agent.py` | the agent's steps: sort, check, fix, ask | change only if you want new steps |
| `demo.py` | simple rules used in demo mode | you can ignore this |

## Day 3: put it online

1. **Upload to GitHub, in your browser.** Open your repository, click **Add file**, then **Upload files**, drag in your project files and click **Commit changes**. Do **not** upload `.streamlit/secrets.toml`.
2. **Deploy.** Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub. Click **Create app**, choose **Deploy a public app from GitHub**, pick your repository and leave the main file as `app.py`.
3. **Add your key safely.** Open **Advanced settings**, and in **Secrets** paste the same three lines you put in `.streamlit/secrets.toml`. Click **Deploy**.
4. **Open your link.** It ends in `streamlit.app`.

To change something later, open the file on GitHub, click the pencil, edit and press **Commit changes**. Your live app updates by itself.

## If something fails

Open your app and click **Manage app** at the bottom right, then read the last lines of the log. Paste them into your AI assistant and ask: "What is wrong, in plain words, and what exact change should I make?"
